from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from .models import Category, Product, Review, WishlistItem, UserProfile, Order, OrderItem
from .forms import PersonalInfoForm, CustomPasswordChangeForm
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import io
import random
import string
from datetime import date, timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Notification, Order
from .models import Cart, CartItem
from decimal import Decimal
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now



TAX_RATE     = Decimal('0.05')
SHIPPING_FEE = Decimal('0.00')


# ── HELPERS ───────────────────────────────────────────────────────────────────
def get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile

def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart

def generate_order_id():
    return '#' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def create_order_notification(order):
    MESSAGES = {
        'pending':    ('Order Placed',    "Your order has been placed successfully! We're getting your item ready for dispatch.", 'order_placed'),
        'processing': ('Order Confirmed', "Your order is confirmed. The seller has approved your order and will ship it soon.",    'order_confirmed'),
        'shipped':    ('On The Way',      "Your order is out for delivery. Track your order for live updates.",                    'on_the_way'),
        'delivered':  ('Delivered',       "Your order has been delivered successfully. Enjoy your purchase!",                     'delivered'),
    }
    if order.status in MESSAGES:
        title, message, status = MESSAGES[order.status]
        Notification.objects.get_or_create(
            user=order.user, order=order, status=status,
            defaults={'title': title, 'message': message, 'is_completed': order.status == 'delivered'}
        )


# ── HOME ──────────────────────────────────────────────────────────────────────


# =========================
# HOME PAGE
# =========================

def index(request):
    # Show success popup if login successful
    login_success = request.session.pop("login_success", False)

    # Fetch real database data
    categories = list(Category.objects.all()[:5])
    deal_products = list(Product.objects.filter(discount_percent__gt=0)[:3])
    reviews = list(Review.objects.all()[:3])

    # ---------------- FALLBACK DATA ---------------- #

    if len(categories) == 0:
        categories = [
            {'name': 'Vegetables', 'image': None},
            {'name': 'Fresh Fruits', 'image': None},
            {'name': 'Milk & Egg', 'image': None},
            {'name': 'Dry Fruits', 'image': None},
            {'name': 'Household', 'image': None},
        ]

    if len(deal_products) == 0:
        deal_products = [
            {
                'name': 'Accessories',
                'subtitle': 'Engine and Tyres',
                'price': 56,
                'rating': 4.5,
                'discount_percent': 20,
                'quantity_info': 'Weight 2.5t',
                'image': None
            },
            {
                'name': 'Accessories Gadgets',
                'subtitle': 'Electronic combo Accessories',
                'price': 56,
                'rating': 4.5,
                'discount_percent': 20,
                'quantity_info': '10 sets',
                'image': None
            },
            {
                'name': 'Life Style',
                'subtitle': 'T-shirt & combo sets',
                'price': 56,
                'rating': 4.5,
                'discount_percent': 20,
                'quantity_info': '3 sets',
                'image': None
            },
        ]

    if len(reviews) == 0:
        reviews = [
            {
                'reviewer_name': 'John Das',
                'rating': 5,
                'short_text': 'Great product quality every time.',
                'full_text': 'All items were fresh and exactly as shown.',
                'image': None
            },
            {
                'reviewer_name': 'Liyanas',
                'rating': 5,
                'short_text': 'Affordable prices and good offers.',
                'full_text': 'There are always great discounts and combo packs.',
                'image': None
            },
            {
                'reviewer_name': 'Andreya',
                'rating': 5,
                'short_text': 'Superfast delivery, totally impressed!',
                'full_text': 'I received my order in just 12 minutes.',
                'image': None
            },
        ]

    context = {
        'categories': categories,
        'deal_products': deal_products,
        'reviews': reviews,
        'login_success': login_success,
    }

    return render(request, 'eshop/index.html', context)
# =========================
# STATIC PAGES
# =========================
def categories(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    return render(request, 'eshop/categories.html', {
        'products': products,
        'categories': categories
    })



def blog(request):
    return render(request, 'eshop/blog.html')


def contact(request):
    return render(request, 'eshop/contact.html')


def about(request):
    return render(request, 'eshop/about.html')


def seller_home(request):
    return render(request, 'eshop/seller.html')


def seller_register(request):
    return render(request, 'eshop/sellerregister.html')


# =========================
# ENQUIRY PAGE
# =========================
def enquiry(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        mobile = request.POST.get('mobile')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"""
Name: {first_name} {last_name}
Mobile: {mobile}
Email: {email}

Message:
{message}
"""

        try:
            send_mail(
                subject,
                full_message,
                email,
                ['your_email@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, "Enquiry sent successfully!")
        except:
            messages.error(request, "Failed to send enquiry.")

        return redirect('eshop:index')

    return render(request, 'eshop/enquiry.html')


# =========================
# LOGIN
# =========================
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("eshop:index")
        else:
            messages.error(request, "Invalid email or password")

    return redirect("eshop:index")


# =========================
# SIGNUP
# =========================
def signup_view(request):
    if request.method == "POST":
        fullname = request.POST.get("fullname")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("eshop:index")

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect("eshop:index")

        try:
            User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=fullname
            )
            messages.success(request, "Signup successful! Please login.")
        except IntegrityError:
            messages.error(request, "Email already exists")

    return redirect("eshop:index")


# =========================
# LOGOUT
# =========================
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect("eshop:index")




# ── WISHLIST PAGE ─────────────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
def wishlist(request):
    items = WishlistItem.objects.filter(
        user=request.user
    ).select_related('product')

    return render(request, 'eshop/wishlist.html', {
        'wishlist_items': items,
        'wishlist_link':  request.build_absolute_uri('/wishlist/'),
    })


# ── TOGGLE WISHLIST (add / remove) — AJAX ─────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def wishlist_toggle(request):
    """
    POST { "product_id": 5 }
    Returns JSON { "added": true/false, "wishlist_count": N }
    """
    try:
        data       = json.loads(request.body)
        product_id = int(data.get('product_id'))
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    product = get_object_or_404(Product, pk=product_id)
    item, created = WishlistItem.objects.get_or_create(
        user=request.user, product=product
    )

    if not created:
        # already in wishlist — remove it
        item.delete()
        added = False
    else:
        added = True

    count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'added': added, 'wishlist_count': count})


# ── REMOVE SINGLE ITEM ─────────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def wishlist_remove(request, product_id):
    """
    Called from the wishlist page to remove one item.
    Returns JSON { "removed": true, "wishlist_count": N }
    """
    WishlistItem.objects.filter(
        user=request.user, product_id=product_id
    ).delete()

    count = WishlistItem.objects.filter(user=request.user).count()
    return JsonResponse({'removed': True, 'wishlist_count': count})


# ── CLEAR ENTIRE WISHLIST ──────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def wishlist_clear(request):
    """
    Deletes all wishlist items for the logged-in user.
    Returns JSON { "cleared": true }
    """
    WishlistItem.objects.filter(user=request.user).delete()
    return JsonResponse({'cleared': True, 'wishlist_count': 0})




# ── PROFILE DASHBOARD ─────────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
def profile_dashboard(request):
    profile = get_or_create_profile(request.user)
    info_form = PersonalInfoForm(instance=profile, user=request.user)
    pwd_form  = CustomPasswordChangeForm(user=request.user)
    orders    = Order.objects.filter(user=request.user).prefetch_related('items__product')

    # which tab to show after form submit
    active_tab = request.GET.get('tab', 'personal')

    return render(request, 'eshop/profile_dashboard.html', {
        'profile':     profile,
        'info_form':   info_form,
        'pwd_form':    pwd_form,
        'orders':      orders,
        'active_tab':  active_tab,
    })


# ── UPDATE PERSONAL INFO (AJAX) ───────────────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def profile_update_info(request):
    profile   = get_or_create_profile(request.user)
    info_form = PersonalInfoForm(request.POST, request.FILES, instance=profile, user=request.user)

    if info_form.is_valid():
        info_form.save()
        return JsonResponse({'success': True, 'message': 'Profile updated successfully!'})

    errors = {field: error[0] for field, error in info_form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors}, status=400)


# ── CHANGE PASSWORD (AJAX) ────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def profile_change_password(request):
    pwd_form = CustomPasswordChangeForm(user=request.user, data=request.POST)

    if pwd_form.is_valid():
        pwd_form.save()
        update_session_auth_hash(request, pwd_form.user)   # keep user logged in
        return JsonResponse({'success': True, 'message': 'Password changed successfully!'})

    errors = {field: error[0] for field, error in pwd_form.errors.items()}
    return JsonResponse({'success': False, 'errors': errors}, status=400)


# ── DOWNLOAD INVOICE (PDF) ────────────────────────────────────────────────────
@login_required(login_url='eshop:login')
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    items = order.items.all()

    try:
        # Try reportlab if installed: pip install reportlab
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=A4,
                                   rightMargin=2*cm, leftMargin=2*cm,
                                   topMargin=2*cm, bottomMargin=2*cm)
        styles  = getSampleStyleSheet()
        story   = []

        # ── Header ──
        title_style = ParagraphStyle('Title', parent=styles['Heading1'],
                                     textColor=colors.HexColor('#00a650'), fontSize=22,
                                     spaceAfter=6)
        story.append(Paragraph('SELLER E-COM', title_style))
        story.append(Paragraph('Tax Invoice / Order Receipt', styles['Normal']))
        story.append(Spacer(1, 0.5*cm))

        # ── Order meta table ──
        delivery_str = order.estimated_delivery.strftime('%d %B %Y') if order.estimated_delivery else 'TBD'
        meta = [
            ['Order ID',    'Payment Method',    'Transaction ID',   'Est. Delivery'],
            [order.order_id, order.payment_method, order.transaction_id or '—', delivery_str],
        ]
        meta_table = Table(meta, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#00a650')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 10),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('PADDING',    (0,0), (-1,-1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.6*cm))

        # ── Items table ──
        story.append(Paragraph('Order Items', styles['Heading2']))
        story.append(Spacer(1, 0.2*cm))
        item_data = [['Product', 'Qty', 'Unit Price', 'Subtotal']]
        for item in items:
            item_data.append([item.name, str(item.quantity),
                               f'${item.price}', f'${item.subtotal()}'])

        item_table = Table(item_data, colWidths=[8*cm, 2*cm, 3*cm, 3*cm])
        item_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#222222')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,-1), 10),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('PADDING',    (0,0), (-1,-1), 8),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 0.4*cm))

        # ── Totals ──
        totals = [
            ['Shipping', f'${order.shipping_cost}'],
            ['Total',    f'${order.total_amount}'],
        ]
        totals_table = Table(totals, colWidths=[13*cm, 3*cm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME',  (0,1), (-1,1), 'Helvetica-Bold'),
            ('FONTSIZE',  (0,0), (-1,-1), 11),
            ('ALIGN',     (1,0), (1,-1), 'RIGHT'),
            ('LINEABOVE', (0,1), (-1,1), 1, colors.HexColor('#00a650')),
            ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#00a650')),
            ('PADDING',   (0,0), (-1,-1), 6),
        ]))
        story.append(totals_table)
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph('Thank you for shopping with Seller E-COM!', styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.pdf"'
        return response

    except ImportError:
        # Fallback plain-text invoice if reportlab not installed
        lines = [
            'SELLER E-COM — Invoice',
            '=' * 40,
            f'Order ID:          {order.order_id}',
            f'Payment Method:    {order.payment_method}',
            f'Transaction ID:    {order.transaction_id or "—"}',
            f'Est. Delivery:     {order.estimated_delivery or "TBD"}',
            f'Status:            {order.get_status_display()}',
            '',
            'Items:',
            '-' * 40,
        ]
        for item in items:
            lines.append(f'  {item.name} × {item.quantity}  @ ${item.price}  = ${item.subtotal()}')
        lines += [
            '-' * 40,
            f'Shipping:  ${order.shipping_cost}',
            f'TOTAL:     ${order.total_amount}',
            '',
            'Thank you for shopping with Seller E-COM!',
        ]
        response = HttpResponse('\n'.join(lines), content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}.txt"'
        return response

def order_notifications(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    history = order.history.order_by('timestamp')

    return render(request, 'eshop/notifications.html', {
        'order': order,
        'history': history
    })


def track_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    steps = ['placed', 'confirmed', 'processing', 'shipping', 'delivered']
    current_index = steps.index(order.status)

    return render(request, 'eshop/track_order.html', {
        'order': order,
        'steps': steps,
        'current_index': current_index
    })



from django.shortcuts import render, get_object_or_404
from .models import Order

# 🔔 Notification Page
def order_notifications(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    # Get all status history (old → latest)
    history = order.history.order_by('timestamp')

    return render(request, 'eshop/notifications.html', {
        'order': order,
        'history': history
    })


# 📦 Order Tracking Page
def track_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    steps = ['placed', 'confirmed', 'processing', 'shipping', 'delivered']
    current_index = steps.index(order.status)

    return render(request, 'eshop/track_order.html', {
        'order': order,
        'steps': steps,
        'current_index': current_index
    })


# 🏠 Optional Home Page (IMPORTANT to avoid error)
def index(request):
    # Get latest order (you can customize later for logged-in user)
    order = Order.objects.order_by('-created_at').first()

    return render(request, 'eshop/index.html', {
        'order': order
    })




@login_required(login_url='eshop:login')
def notifications(request):
    notis        = Notification.objects.filter(user=request.user)
    unread_count = notis.filter(is_read=False).count()
    return render(request, 'eshop/notifications.html', {
        'notifications': notis,
        'unread_count':  unread_count,
    })

@login_required(login_url='eshop:login')
@require_POST
def notification_read(request, noti_id):
    Notification.objects.filter(id=noti_id, user=request.user).update(is_read=True)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'success': True, 'unread_count': unread})

@login_required(login_url='eshop:login')
@require_POST
def notification_read_all(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True, 'unread_count': 0})

@login_required(login_url='eshop:login')
def order_status(request):
    search_order_id = request.GET.get('order_id', '').strip()
    order = None
    steps = []
    STEP_SEQUENCE = [
        ('order_placed',    'Order Placed'),
        ('order_confirmed', 'Accepted'),
        ('in_progress',     'In Progress'),
        ('on_the_way',      'On The Way'),
        ('delivered',       'Delivered'),
    ]
    STATUS_TO_STEP = {
        'pending': 0, 'processing': 1,
        'shipped': 3, 'delivered': 4, 'cancelled': 0,
    }
    if search_order_id:
        try:
            order = Order.objects.prefetch_related('items__product').get(
                order_id__iexact=search_order_id, user=request.user)
            current_step_idx = STATUS_TO_STEP.get(order.status, 0)
            estimated = order.estimated_delivery
            for i, (key, label) in enumerate(STEP_SEQUENCE):
                if i < current_step_idx:
                    noti = Notification.objects.filter(order=order, status=key).first()
                    ts   = noti.created_at if noti else order.created_at
                    steps.append({'label': label, 'state': 'done',
                                  'timestamp': ts.strftime('%d %B  %Y'),
                                  'time': ts.strftime('%I:%M %p'), 'expected_date': ''})
                elif i == current_step_idx:
                    steps.append({'label': label, 'state': 'active',
                                  'timestamp': order.created_at.strftime('%d %B  %Y'),
                                  'time': order.created_at.strftime('%I:%M %p'), 'expected_date': ''})
                else:
                    exp = estimated.strftime('%d %B  %Y') if estimated else 'TBD'
                    steps.append({'label': label, 'state': 'pending',
                                  'timestamp': '', 'time': '', 'expected_date': exp})
        except Order.DoesNotExist:
            order = None
    return render(request, 'eshop/order_status.html', {
        'order': order, 'steps': steps, 'search_order_id': search_order_id,
    })

# ── UTILITY: call this whenever order status is updated ──────────────────────
def create_order_notification(order):
    """
    Auto-creates a Notification when an order status changes.
    Call from admin action or order update view:

        from .views_notifications import create_order_notification
        order.status = 'processing'
        order.save()
        create_order_notification(order)
    """
    MESSAGES = {
        'pending':    ('Order Placed',
                       "Your order has been placed successfully!\nWe're getting your item ready for dispatch."),
        'processing': ('Order Confirmed',
                       "Your order is confirmed.\nThe seller has approved your order and will ship it soon."),
        'shipped':    ('On The Way',
                       "Your order is out for delivery. Track your order for live updates."),
        'delivered':  ('Delivered',
                       "Your order has been delivered successfully. Enjoy your purchase!"),
        'cancelled':  ('Order Cancelled',
                       "Your order has been cancelled. Contact support if you need help."),
    }

    STATUS_TO_NOTI = {
        'pending':    'order_placed',
        'processing': 'order_confirmed',
        'shipped':    'on_the_way',
        'delivered':  'delivered',
        'cancelled':  'order_placed',
    }

    if order.status in MESSAGES:
        title, message = MESSAGES[order.status]
        Notification.objects.get_or_create(
            user=order.user,
            order=order,
            status=STATUS_TO_NOTI.get(order.status, 'order_placed'),
            defaults={
                'title':        title,
                'message':      message,
                'is_completed': order.status in ('delivered',),
            }
        )




TAX_RATE     = Decimal('0.05')   # 5%
SHIPPING_FEE = Decimal('0.00')   # free shipping


# ══════════════════════════════════════════════════════════════════════════════
# CART VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@login_required(login_url='eshop:login')
def cart_view(request):
    cart       = get_or_create_cart(request.user)
    cart_items = cart.items.select_related('product').all()

    # get coupon discount from session
    discount      = Decimal(str(request.session.get('coupon_discount', '0')))
    coupon_code   = request.session.get('coupon_code', '')

    subtotal = cart.get_subtotal()
    taxes    = round(subtotal * TAX_RATE, 2)
    shipping = SHIPPING_FEE
    total    = round(subtotal - discount + taxes + shipping, 2)

    return render(request, 'eshop/cart.html', {
        'cart_items':   cart_items,
        'subtotal':     subtotal,
        'taxes':        taxes,
        'shipping':     shipping,
        'discount':     discount,
        'coupon_code':  coupon_code,
        'total':        total,
    })


@login_required(login_url='eshop:login')
@require_POST
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart    = get_or_create_cart(request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
        item.save()
    return JsonResponse({'success': True, 'cart_count': cart.item_count(), 'added': True})


@login_required(login_url='eshop:login')
@require_POST
def cart_update(request):
    data     = json.loads(request.body)
    item_id  = data.get('item_id')
    quantity = int(data.get('quantity', 1))
    item     = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.quantity = max(1, quantity)
    item.save()

    cart         = item.cart
    discount     = Decimal(str(request.session.get('coupon_discount', '0')))
    subtotal     = cart.get_subtotal()
    taxes        = round(subtotal * TAX_RATE, 2)
    total        = round(subtotal - discount + taxes + SHIPPING_FEE, 2)

    return JsonResponse({
        'item_subtotal': float(item.get_subtotal()),
        'subtotal':      float(subtotal),
        'taxes':         float(taxes),
        'total':         float(total),
        'item_count':    cart.item_count(),
    })


@login_required(login_url='eshop:login')
@require_POST
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    cart     = get_or_create_cart(request.user)
    discount = Decimal(str(request.session.get('coupon_discount', '0')))
    subtotal = cart.get_subtotal()
    taxes    = round(subtotal * TAX_RATE, 2)
    total    = round(subtotal - discount + taxes + SHIPPING_FEE, 2)
    return JsonResponse({
        'success': True, 'subtotal': float(subtotal),
        'taxes': float(taxes), 'total': float(total),
        'item_count': cart.item_count(),
    })


@login_required(login_url='eshop:login')
@require_POST
def cart_clear(request):
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()
    request.session.pop('coupon_discount', None)
    request.session.pop('coupon_code', None)
    return JsonResponse({'success': True})


@login_required(login_url='eshop:login')
@require_POST
def cart_coupon(request):
    data = json.loads(request.body)
    code = data.get('code', '').upper().strip()
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invalid or expired coupon code.'})

    cart     = get_or_create_cart(request.user)
    subtotal = cart.get_subtotal()
    discount = min(coupon.discount, subtotal)
    taxes    = round((subtotal - discount) * TAX_RATE, 2)
    new_total= round(subtotal - discount + taxes + SHIPPING_FEE, 2)

    # save in session
    request.session['coupon_discount'] = str(discount)
    request.session['coupon_code']     = code

    return JsonResponse({
        'success':   True,
        'discount':  float(discount),
        'new_total': float(new_total),
        'taxes':     float(taxes),
        'message':   f'Coupon "{code}" applied! You saved ${discount}',
    })


# ── CHECKOUT (save billing + create order) ────────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def checkout_submit(request):
    data = json.loads(request.body)

    # validate required fields
    required = ['first_name','last_name','country','phone','email','street','delivery']
    errors   = {}
    for field in required:
        if not data.get(field, '').strip():
            errors[field] = f'{field.replace("_"," ").title()} is required.'
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # save billing in session for payment step
    request.session['billing'] = data
    return JsonResponse({'success': True})


# ── PLACE ORDER (after payment method chosen) ─────────────────────────────────
@login_required(login_url='eshop:login')
@require_POST
def place_order(request):
    data           = json.loads(request.body)
    payment_method = data.get('payment_method', 'COD').upper()
    transaction_id = data.get('transaction_id', '')
    billing        = request.session.get('billing', {})

    cart       = get_or_create_cart(request.user)
    cart_items = cart.items.select_related('product').all()

    if not cart_items.exists():
        return JsonResponse({'success': False, 'message': 'Your cart is empty.'}, status=400)

    discount  = Decimal(str(request.session.get('coupon_discount', '0')))
    subtotal  = cart.get_subtotal()
    taxes     = round(subtotal * TAX_RATE, 2)
    shipping  = SHIPPING_FEE
    total     = round(subtotal - discount + taxes + shipping, 2)

    # create order
    order = Order.objects.create(
        user               = request.user,
        order_id           = generate_order_id(),
        payment_method     = payment_method,
        transaction_id     = transaction_id,
        status             = 'pending',
        shipping_cost      = shipping,
        total_amount       = total,
        estimated_delivery = date.today() + timedelta(days=5),
        billing_first_name = billing.get('first_name', ''),
        billing_last_name  = billing.get('last_name', ''),
        billing_email      = billing.get('email', ''),
        billing_phone      = billing.get('phone', ''),
        billing_address    = billing.get('delivery', ''),
        billing_country    = billing.get('country', ''),
        billing_state      = billing.get('state', ''),
        billing_zip        = billing.get('zip', ''),
    )

    # create order items from cart
    for item in cart_items:
        OrderItem.objects.create(
            order    = order,
            product  = item.product,
            name     = item.product.name,
            price    = item.product.price,
            quantity = item.quantity,
        )

    # clear cart and session
    cart.items.all().delete()
    request.session.pop('coupon_discount', None)
    request.session.pop('coupon_code', None)
    request.session.pop('billing', None)

    # create notification
    create_order_notification(order)

    return JsonResponse({
        'success':  True,
        'order_id': order.order_id,
        'message':  f'Order {order.order_id} placed successfully!',
    })



def add_to_cart(request, product_id):
    if request.method == "POST":
        product = Product.objects.get(id=product_id)

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        cart_count = CartItem.objects.filter(cart=cart).count()

        return JsonResponse({
            "added": True,
            "cart_count": cart_count
        })

    return JsonResponse({"added": False})




client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_razorpay_order(request):
    if request.method == "POST":
        try:
            # ⚠️ TEMP: hardcode for testing
            amount = 6300  # ₹63 → in paise

            order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": 1
            })

            return JsonResponse({
                "success": True,
                "order_id": order["id"],
                "amount": amount,
                "key": settings.RAZORPAY_KEY_ID
            })

        except Exception as e:
            print("ERROR:", e)  # 👈 check terminal
            return JsonResponse({"success": False, "error": str(e)})


@csrf_exempt
def verify_razorpay_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            params_dict = {
                "razorpay_order_id": data.get("razorpay_order_id"),
                "razorpay_payment_id": data.get("razorpay_payment_id"),
                "razorpay_signature": data.get("razorpay_signature")
            }

            client.utility.verify_payment_signature(params_dict)

            # ✅ CREATE ORDER
            order = Order.objects.create(
                user=request.user,
                order_id=params_dict["razorpay_order_id"],
                razorpay_payment_id=params_dict["razorpay_payment_id"],
                total_amount=63,  # replace with real total
            )

            return JsonResponse({
                "success": True,
                "order": {
                    "order_id": order.order_id,
                    "payment_id": order.razorpay_payment_id,
                    "amount": order.total_amount,
                    "date": order.created_at.strftime("%b %d, %Y %I:%M %p")
                }
            })

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})



def filter_products(request):
    import json
    data = json.loads(request.body)

    categories = data.get('categories', [])

    products = Product.objects.all()

    if categories:
        products = products.filter(category__slug__in=categories)

    product_data = [
        {
            "id": p.id,
            "name": p.name,
            "price": str(p.price),
            "image": p.image.url if p.image else ""
        }
        for p in products
    ]

    return JsonResponse({"products": product_data})



def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    gallery_images = product.gallery.all()

    context = {
        'product': product,
        'gallery_images': gallery_images
    }

    return render(request, 'eshop/product_detail.html', context)