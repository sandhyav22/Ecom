from django.urls import path
from . import views

app_name = 'eshop'

urlpatterns = [

    # ── Main pages ──────────────────────────────────────
    path('',                views.index,            name='index'),
    path('categories/',     views.categories,       name='categories'),
    path('blog/',           views.blog,             name='blog'),
    path('contact/',        views.contact,          name='contact'),
    path('about/',          views.about,            name='about'),
    path('login/',          views.login_view,       name='login'),
    path('logout/',         views.logout_view,      name='logout'),
    path('signup/',         views.signup_view,      name='signup'),
    path('enquiry/',        views.enquiry,          name='enquiry'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    

    # ── Seller ──────────────────────────────────────────
    path('seller/',         views.seller_home,      name='seller_home'),
    path('seller-register/',views.seller_register,  name='seller_register'),

    # ── Profile ─────────────────────────────────────────
    path('profile/',                         views.profile_dashboard,       name='profile'),
    path('profile/update-info/',             views.profile_update_info,     name='profile_update_info'),
    path('profile/change-password/',         views.profile_change_password, name='profile_change_password'),
    path('profile/invoice/<str:order_id>/',  views.download_invoice,        name='download_invoice'),

    # ── Wishlist ─────────────────────────────────────────
    path('wishlist/',                         views.wishlist,        name='wishlist'),
    path('wishlist/toggle/',                  views.wishlist_toggle, name='wishlist_toggle'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    path('wishlist/clear/',                   views.wishlist_clear,  name='wishlist_clear'),

    # ── Notifications ────────────────────────────────────
    path('notifications/',                       views.notifications,         name='notifications'),
    path('notifications/read/<int:noti_id>/',    views.notification_read,     name='notification_read'),
    path('notifications/read-all/',              views.notification_read_all, name='notification_read_all'),

    # ── Order Status ─────────────────────────────────────
    path('order-status/',                        views.order_status,          name='order_status'),

    # ── Cart ─────────────────────────────────────────────
    path('cart/',                         views.cart_view,       name='cart'),
    path('cart/add/<int:product_id>/',    views.cart_add,        name='cart_add'),
    path('cart/update/',                  views.cart_update,     name='cart_update'),
    path('cart/remove/<int:item_id>/',    views.cart_remove,     name='cart_remove'),
    path('cart/clear/',                   views.cart_clear,      name='cart_clear'),
    path('cart/coupon/',                  views.cart_coupon,     name='cart_coupon'),
    path('cart/checkout/',                views.checkout_submit, name='checkout_submit'),
    path('cart/place-order/',             views.place_order,     name='place_order'),


    path("create-razorpay-order/", views.create_razorpay_order, name="create_razorpay_order"),
path("verify-razorpay-payment/", views.verify_razorpay_payment, name="verify_razorpay_payment"),
]
