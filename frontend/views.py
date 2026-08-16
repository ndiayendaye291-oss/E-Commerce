from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from catalog.models import Product, Category
from cart.models import Cart, CartItem
from .forms import CustomUserCreationForm

def index(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'frontend/index.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie !")
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'frontend/register.html', {'form': form})

@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'frontend/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        messages.error(request, f"Désolé, le produit {product.name} est en rupture de stock.")
        return redirect('index')
        
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        if cart_item.quantity >= product.stock:
            messages.error(request, f"Vous ne pouvez pas ajouter plus de {product.name} (Stock max atteint).")
            return redirect('index')
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} ajouté au panier.")
    return redirect('index')

@login_required
def checkout(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    if not cart.items.exists():
        messages.warning(request, "Votre panier est vide.")
        return redirect('index')
    
    if request.method == 'POST':
        # Create Order
        address = request.POST.get('address', request.user.address)
        payment_method = request.POST.get('payment_method', 'CASH')
        
        from orders.models import Order, OrderItem, Payment
        
        order = Order.objects.create(
            user=request.user,
            shipping_address=address,
            total_amount=sum(item.total_price for item in cart.items.all())
        )
        
        # Create OrderItems and reduce stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.price
            )
            # Reduce stock
            item.product.stock -= item.quantity
            item.product.save()
            
        # Create Payment
        Payment.objects.create(
            order=order,
            amount=order.total_amount,
            method=payment_method,
            is_successful=True if payment_method == 'CASH' else False
        )
        
        # Create Delivery (if applicable, let's create a pending delivery)
        from delivery.models import Delivery
        Delivery.objects.create(order=order)
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, "Commande validée avec succès !")
        return redirect('dashboard')
        
    return render(request, 'frontend/checkout.html', {'cart': cart})

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'DELIVERY':
        from delivery.models import Delivery
        deliveries = Delivery.objects.filter(delivery_person=user)
        return render(request, 'frontend/dashboard_delivery.html', {'deliveries': deliveries})
    else:
        from orders.models import Order
        orders = Order.objects.filter(user=user).order_by('-created_at')
        return render(request, 'frontend/dashboard_client.html', {'orders': orders})

@login_required
def complete_delivery(request, delivery_id):
    if request.user.role != 'DELIVERY':
        messages.error(request, "Accès non autorisé.")
        return redirect('index')
        
    from delivery.models import Delivery
    delivery = get_object_or_404(Delivery, id=delivery_id, delivery_person=request.user)
    
    if request.method == 'POST':
        delivery.status = 'DELIVERED'
        delivery.save()
        
        # Mettre à jour le statut de la commande correspondante
        delivery.order.status = 'DELIVERED'
        delivery.order.save()
        
        messages.success(request, f"La livraison #{delivery.id} a été marquée comme terminée.")
        
    return redirect('dashboard')
