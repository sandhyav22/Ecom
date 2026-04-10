from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Category(models.Model):
    name  = models.CharField(max_length=200)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    def __str__(self): return self.name


class Product(models.Model):
    name             = models.CharField(max_length=200)
    subtitle         = models.CharField(max_length=255, blank=True)
    description      = models.TextField(blank=True)
    price            = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.PositiveIntegerField(default=0)
    rating           = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    quantity_info    = models.CharField(max_length=100, blank=True)
    size             = models.CharField(max_length=50, blank=True)
    image            = models.ImageField(upload_to='products/', blank=True, null=True)
    in_stock         = models.BooleanField(default=True)
    category         = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
class ProductGallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return self.product.name

class Review(models.Model):
    reviewer_name = models.CharField(max_length=100)
    rating        = models.PositiveIntegerField(default=5)
    short_text    = models.CharField(max_length=200)
    full_text     = models.TextField()
    created_at    = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.reviewer_name} — {self.rating}★"


class WishlistItem(models.Model):
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist_items')
    product    = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlisted_by')
    date_added = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('user', 'product')
        ordering        = ['-date_added']
    def __str__(self): return f"{self.user.username} → {self.product.name}"


# ── CART ──────────────────────────────────────────────────────────────────────
class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Cart — {self.user.username}"

    def get_subtotal(self):
        return sum(item.get_subtotal() for item in self.items.select_related('product').all())

    def get_taxes(self, rate=Decimal('0.05')):
        return round(self.get_subtotal() * rate, 2)

    def get_total(self, shipping=Decimal('0')):
        return round(self.get_subtotal() + self.get_taxes() + shipping, 2)

    def item_count(self):
        return self.items.count()


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def get_subtotal(self):
        return round(self.product.price * self.quantity, 2)

    def __str__(self): return f"{self.product.name} × {self.quantity}"


# ── USER PROFILE ──────────────────────────────────────────────────────────────
class UserProfile(models.Model):
    GENDER_CHOICES = [('M','Male'),('F','Female'),('O','Other')]
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone      = models.CharField(max_length=15, blank=True)
    gender     = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"Profile — {self.user.username}"
    def get_full_name(self): return f"{self.user.first_name} {self.user.last_name}".strip()


# ── ORDER ─────────────────────────────────────────────────────────────────────
class Order(models.Model):
    STATUS_CHOICES  = [
        ('pending','Pending'),('processing','Processing'),
        ('shipped','Shipped'),('delivered','Delivered'),('cancelled','Cancelled')
    ]

    PAYMENT_CHOICES = [
        ('G-PAY','Google Pay'),('PHONEPE','PhonePe'),
        ('PAYTM','Paytm'),('COD','Cash on Delivery'),('CARD','Card')
    ]

    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_id       = models.CharField(max_length=20, unique=True)

    # ✅ UPDATE THIS
    payment_method = models.CharField(max_length=20, default='RAZORPAY')

    # ✅ KEEP THIS (use for payment_id)
    transaction_id = models.CharField(max_length=100, blank=True)

    # ✅ ADD THESE (IMPORTANT)
    razorpay_order_id   = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature  = models.CharField(max_length=255, blank=True, null=True)

    status        = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total_amount  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery = models.DateField(null=True, blank=True)

    # billing snapshot
    billing_first_name = models.CharField(max_length=50, blank=True)
    billing_last_name  = models.CharField(max_length=50, blank=True)
    billing_email      = models.EmailField(blank=True)
    billing_phone      = models.CharField(max_length=15, blank=True)
    billing_address    = models.TextField(blank=True)
    billing_country    = models.CharField(max_length=50, blank=True)
    billing_state      = models.CharField(max_length=50, blank=True)
    billing_zip        = models.CharField(max_length=10, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_id} — {self.user.username}"

    def calculate_total(self):
        subtotal = sum(item.subtotal() for item in self.items.all())
        self.total_amount = subtotal + self.shipping_cost
        self.save()
        return self.total_amount

class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    name     = models.CharField(max_length=200)
    price    = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image    = models.ImageField(upload_to='order_items/', blank=True, null=True)

    def subtotal(self): return self.price * self.quantity
    def __str__(self): return f"{self.name} × {self.quantity}"


# ── NOTIFICATION ──────────────────────────────────────────────────────────────
class Notification(models.Model):
    STATUS_CHOICES = [
        ('order_placed',    'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('in_progress',     'In Progress'),
        ('on_the_way',      'On The Way'),
        ('delivered',       'Delivered'),
    ]
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    order        = models.ForeignKey(Order, on_delete=models.CASCADE,
                                     related_name='notifications', null=True, blank=True)
    title        = models.CharField(max_length=100)
    message      = models.TextField()
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='order_placed')
    is_read      = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta: ordering = ['-created_at']
    def __str__(self): return f"{self.title} — {self.user.username}"


# ── COUPON ────────────────────────────────────────────────────────────────────
class Coupon(models.Model):
    code       = models.CharField(max_length=20, unique=True)
    discount   = models.DecimalField(max_digits=6, decimal_places=2)  # flat amount
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.code} — ${self.discount} off"
