from django.contrib import admin
from django.urls import path, include
from ecom.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Product URLs
    path('', product_list, name='product_list'),
    path('products/', product_list, name='product_list'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('search/', search_results, name='search_results'),
    path('products/<int:product_id>/suggest-tags/', suggest_tags, name='suggest_tags'),
    
    # Cart URLs
    path('cart/', cart_view, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),
    
    # Order URLs
    path('checkout/', checkout, name='checkout'),
    path('orders/', order_list, name='order_list'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    
    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', register, name='register'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)