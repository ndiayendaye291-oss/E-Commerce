from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='frontend/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('add-product/', views.add_product, name='add_product'),
    path('complete-delivery/<int:delivery_id>/', views.complete_delivery, name='complete_delivery'),
    path('assign-delivery/<int:order_id>/', views.assign_delivery, name='assign_delivery'),
    path('request-role/<str:role>/', views.request_role, name='request_role'),
    path('approve-role/<int:user_id>/<str:action>/', views.approve_role, name='approve_role'),
    path('create-admin/', views.create_admin, name='create_admin'),
    path('pos/', views.pos_checkout, name='pos_checkout'),
    path('api/check-orders/', views.api_check_orders, name='api_check_orders'),
    path('change-language/<str:lang_code>/', views.change_language, name='change_language'),

    # Superadmin Control Center URLs
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/user/<int:user_id>/toggle-block/', views.superadmin_toggle_block_user, name='superadmin_toggle_block_user'),
    path('superadmin/user/<int:user_id>/change-role/', views.superadmin_change_user_role, name='superadmin_change_user_role'),
    path('superadmin/order/<int:order_id>/status/', views.superadmin_override_order_status, name='superadmin_override_order_status'),
    path('superadmin/product/<int:product_id>/toggle-status/', views.superadmin_toggle_product_status, name='superadmin_toggle_product_status'),
]

