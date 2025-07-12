from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from .models import Product, Cart, CartItem, Order, OrderItem, Tag
import json

# Product Views
def product_list(request):
    """Display all products with pagination"""
    products = Product.objects.all().order_by('-date_added')
    
    # Pagination
    paginator = Paginator(products, 12)  # Show 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'product_list.html', context)

def product_detail(request, pk):
    """Display product details"""
    product = get_object_or_404(Product, pk=pk)
    
    # Get related products (same tags)
    related_products = Product.objects.filter(
        tags__in=product.tags.all()
    ).exclude(id=product.id).distinct()[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)

def search_results(request):
    """Search products by name, description, or tags"""
    query = request.GET.get('q', '')
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'query': query,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    }
    return render(request, 'search_results.html', context)

# Cart Views
def get_or_create_cart(request):
    """Get or create cart for user"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        # Handle anonymous users with session
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user=None)
                return cart
            except Cart.DoesNotExist:
                pass
        
        # Create new cart for anonymous user
        cart = Cart.objects.create(user=None)
        request.session['cart_id'] = cart.id
        return cart

@require_POST
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock
    if product.stock < quantity:
        messages.error(request, f'Only {product.stock} items available in stock.')
        return redirect('product_detail', pk=product_id)
    
    cart = get_or_create_cart(request)
    
    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Update quantity if item already exists
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            messages.error(request, f'Cannot add more items. Only {product.stock} available.')
            return redirect('product_detail', pk=product_id)
        cart_item.quantity = new_quantity
        cart_item.save()
    
    messages.success(request, f'{product.name} added to cart!')
    return redirect('product_detail', pk=product_id)

def cart_view(request):
    """Display cart contents"""
    cart = get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart)
    
    # Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'cart': cart,
    }
    return render(request, 'cart.html', context)

@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    elif quantity > cart_item.product.stock:
        messages.error(request, f'Only {cart_item.product.stock} items available.')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated.')
    
    return redirect('cart')

def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('cart')

def clear_cart(request):
    """Clear all items from cart"""
    cart = get_or_create_cart(request)
    CartItem.objects.filter(cart=cart).delete()
    messages.success(request, 'Cart cleared.')
    return redirect('cart')

# Order Views
@login_required
def checkout(request):
    """Process checkout"""
    cart = get_or_create_cart(request)
    cart_items = CartItem.objects.filter(cart=cart)
    
    if not cart_items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Calculate total
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        # Check stock before creating order
        for item in cart_items:
            if item.product.stock < item.quantity:
                messages.error(request, f'Insufficient stock for {item.product.name}.')
                return redirect('cart')
        
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=total,
                status=Order.Status.PENDING
            )
            
            # Create order items and update stock
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                
                # Update product stock
                item.product.stock -= item.quantity
                item.product.save()
            
            # Clear cart
            cart_items.delete()
            
            messages.success(request, f'Order #{order.id} placed successfully!')
            return redirect('order_detail', order_id=order.id)
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'checkout.html', context)

@login_required
def order_list(request):
    """Display user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'order_list.html', context)

@login_required
def order_detail(request, order_id):
    """Display order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = OrderItem.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'order_detail.html', context)

# Authentication Views
def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('product_list')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

# AI Tag Suggestion (Optional feature)
@require_POST
def suggest_tags(request, product_id):
    """AI-powered tag suggestion for products"""
    product = get_object_or_404(Product, id=product_id)
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Simple tag suggestion based on product name and description
    # In a real implementation, you'd use an AI service
    suggested_tags = []
    
    # Basic keyword extraction
    text = f"{product.name} {product.description}".lower()
    
    # Sample tag suggestions based on keywords
    tag_keywords = {
        'electronics': ['phone', 'laptop', 'computer', 'electronic', 'tech'],
        'clothing': ['shirt', 'pants', 'dress', 'wear', 'fashion'],
        'books': ['book', 'read', 'novel', 'story', 'literature'],
        'home': ['kitchen', 'bedroom', 'living', 'furniture', 'decor'],
        'sports': ['sport', 'fitness', 'exercise', 'gym', 'athletic'],
        'beauty': ['beauty', 'cosmetic', 'skincare', 'makeup', 'health'],
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in text for keyword in keywords):
            suggested_tags.append(tag)
    
    return JsonResponse({'tags': suggested_tags})

# Context processor for cart count (add this to settings.py)
def cart_context(request):
    """Add cart count to all templates"""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = CartItem.objects.filter(cart=cart).count()
        except Cart.DoesNotExist:
            cart_count = 0
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id, user=None)
                cart_count = CartItem.objects.filter(cart=cart).count()
            except Cart.DoesNotExist:
                cart_count = 0
        else:
            cart_count = 0
    
    return {'cart_count': cart_count}