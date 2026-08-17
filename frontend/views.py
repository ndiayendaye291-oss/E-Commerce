from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q
from catalog.models import Product, Category
from cart.models import Cart, CartItem
from .forms import CustomUserCreationForm, ProductForm

def index(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.all()
    categories = Category.objects.all()
    
    if query:
        products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category_id:
        products = products.filter(category_id=category_id)
        
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': int(category_id) if category_id.isdigit() else None,
    }
    return render(request, 'frontend/index.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'frontend/product_detail.html', {'product': product})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.role in ['SELLER', 'DELIVERY']:
                user.is_approved = False
                user.save()
                messages.warning(request, f"Votre compte {user.get_role_display()} a été créé avec succès ! Il est en attente d'approbation par le Super Admin.")
                return redirect('login')
            else:
                user.is_approved = True
                user.save()
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
        
        # Create Financial Transaction Journal Entry (10% commission, 90% seller)
        from orders.models import Transaction
        from decimal import Decimal
        total = Decimal(str(order.total_amount))
        commission = total * Decimal('0.10')
        seller_share = total * Decimal('0.90')
        
        Transaction.objects.create(
            transaction_id=f"TXN-{order.id:06d}",
            order=order,
            total_amount=total,
            payment_method=payment_method,
            platform_commission=commission,
            seller_amount=seller_share,
            delivery_fee=Decimal('1500.00')
        )
        
        # Create Delivery
        from delivery.models import Delivery
        Delivery.objects.create(order=order)
        
        # Clear cart
        cart.items.all().delete()
        
        messages.success(request, "Commande validée avec succès !")
        return redirect('order_success', order_id=order.id)
        
    return render(request, 'frontend/checkout.html', {'cart': cart})

@login_required
def order_success(request, order_id):
    from orders.models import Order
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'frontend/order_success.html', {'order': order})

@login_required
def dashboard(request):
    user = request.user
    if user.role == 'DELIVERY':
        from delivery.models import Delivery
        deliveries = Delivery.objects.filter(delivery_person=user)
        return render(request, 'frontend/dashboard_delivery.html', {'deliveries': deliveries})
    elif user.role in ['SELLER', 'ADMIN']:
        from orders.models import Order, Transaction
        from accounts.models import CustomUser
        from django.db.models import Sum
        
        products = Product.objects.filter(seller=user) if user.role == 'SELLER' else Product.objects.all()
        orders = Order.objects.all().order_by('-created_at')
        deliverers = CustomUser.objects.filter(role='DELIVERY')
        role_requests = CustomUser.objects.filter(role_request__isnull=False).exclude(role_request='')
        pending_users = CustomUser.objects.filter(is_approved=False)
        
        # Financial Metrics for Admin
        total_revenue = Transaction.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_commission = Transaction.objects.aggregate(Sum('platform_commission'))['platform_commission__sum'] or 0
        total_seller_payout = Transaction.objects.aggregate(Sum('seller_amount'))['seller_amount__sum'] or 0
        total_delivery_fees = Transaction.objects.aggregate(Sum('delivery_fee'))['delivery_fee__sum'] or 0
        
        cash_total = Transaction.objects.filter(payment_method='CASH').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        mobile_total = Transaction.objects.filter(payment_method='MOBILE').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        card_total = Transaction.objects.filter(payment_method='CARD').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        recent_transactions = Transaction.objects.all().order_by('-created_at')[:10]
        
        return render(request, 'frontend/dashboard_seller.html', {
            'products': products, 
            'orders': orders, 
            'deliverers': deliverers,
            'role_requests': role_requests,
            'pending_users': pending_users,
            'total_revenue': total_revenue,
            'total_commission': total_commission,
            'total_seller_payout': total_seller_payout,
            'total_delivery_fees': total_delivery_fees,
            'cash_total': cash_total,
            'mobile_total': mobile_total,
            'card_total': card_total,
            'recent_transactions': recent_transactions,
        })
    else:
        from orders.models import Order
        orders = Order.objects.filter(user=user).order_by('-created_at')
        return render(request, 'frontend/dashboard_client.html', {'orders': orders})

@login_required
def add_product(request):
    if request.user.role not in ['SELLER', 'ADMIN'] and not request.user.is_staff:
        messages.error(request, "Accès réservé aux vendeurs et administrateurs.")
        return redirect('index')
        
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, f"Le produit '{product.name}' a été publié avec succès !")
            return redirect('dashboard')
    else:
        form = ProductForm()
        
    return render(request, 'frontend/add_product.html', {'form': form})

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

@login_required
def assign_delivery(request, order_id):
    if request.user.role not in ['SELLER', 'ADMIN'] and not request.user.is_staff:
        messages.error(request, "Accès réservé aux vendeurs et administrateurs.")
        return redirect('index')
        
    if request.method == 'POST':
        deliverer_id = request.POST.get('deliverer_id')
        from orders.models import Order
        from delivery.models import Delivery
        from accounts.models import CustomUser
        
        order = get_object_or_404(Order, id=order_id)
        delivery, _ = Delivery.objects.get_or_create(order=order)
        
        if deliverer_id:
            deliverer = get_object_or_404(CustomUser, id=deliverer_id, role='DELIVERY')
            delivery.delivery_person = deliverer
            delivery.status = 'ASSIGNED'
            delivery.save()
            
            order.status = 'SHIPPED'
            order.save()
            messages.success(request, f"La commande #{order.id} a été validée et assignée au livreur {deliverer.username} !")
        else:
            messages.warning(request, "Veuillez sélectionner un livreur.")
            
    return redirect('dashboard')

@login_required
def request_role(request, role):
    if role not in ['SELLER', 'DELIVERY']:
        messages.error(request, "Demande de rôle invalide.")
        return redirect('dashboard')
        
    user = request.user
    user.role_request = role
    user.role_request_rejected = False
    user.save()
    messages.success(request, f"Votre demande pour devenir {user.get_role_request_display()} a été envoyée à l'administrateur !")
    return redirect('dashboard')

@login_required
def approve_role(request, user_id, action):
    if request.user.role != 'ADMIN' and not request.user.is_superuser:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard')
        
    from accounts.models import CustomUser
    target_user = get_object_or_404(CustomUser, id=user_id)
    
    if action == 'approve':
        if target_user.role_request:
            target_user.role = target_user.role_request
            target_user.role_request = None
        target_user.is_approved = True
        target_user.role_request_rejected = False
        target_user.save()
        messages.success(request, f"La demande de {target_user.username} a été approuvée avec succès ! Il est désormais {target_user.get_role_display()}.")
    elif action == 'reject':
        target_user.role_request = None
        target_user.role_request_rejected = True
        target_user.save()
        messages.info(request, f"La demande de {target_user.username} a été refusée.")
        
    return redirect('dashboard')

@login_required
def create_admin(request):
    if not request.user.is_superuser and request.user.role != 'ADMIN':
        messages.error(request, "Seul le Super Admin peut créer de nouveaux Administrateurs.")
        return redirect('dashboard')
        
    from .forms import AdminCreationForm
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            new_admin = form.save(commit=False)
            new_admin.role = 'ADMIN'
            new_admin.is_approved = True
            new_admin.is_staff = True
            new_admin.save()
            messages.success(request, f"L'administrateur '{new_admin.username}' a été créé avec les permissions personnalisées !")
            return redirect('dashboard')
    else:
        form = AdminCreationForm()
        
    return render(request, 'frontend/create_admin.html', {'form': form})

from django.http import JsonResponse

@login_required
def api_check_orders(request):
    if request.user.role not in ['SELLER', 'ADMIN'] and not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    from orders.models import Order
    latest_order = Order.objects.order_by('-created_at').first()
    count = Order.objects.count()
    
    return JsonResponse({
        'count': count,
        'latest_id': latest_order.id if latest_order else 0,
        'latest_user': latest_order.user.username if latest_order else '',
        'latest_amount': str(latest_order.total_amount) if latest_order else '0',
    })

@login_required
def pos_checkout(request):
    if request.user.role not in ['SELLER', 'ADMIN'] and not request.user.is_staff:
        messages.error(request, "Accès réservé aux vendeurs et administrateurs.")
        return redirect('index')
        
    products = Product.objects.filter(stock__gt=0)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        payment_method = request.POST.get('payment_method', 'CASH')
        client_name = request.POST.get('client_name', 'Client Magasin')
        
        product = get_object_or_404(Product, id=product_id)
        
        if quantity > product.stock:
            messages.error(request, f"Stock insuffisant ({product.stock} disponibles).")
            return redirect('pos_checkout')
            
        from orders.models import Order, OrderItem, Payment, Transaction
        from decimal import Decimal
        
        # Create In-Store Order
        total = Decimal(str(product.price)) * Decimal(str(quantity))
        order = Order.objects.create(
            user=request.user,
            status='DELIVERED',
            shipping_address=f"Vente Directe en Magasin - Client: {client_name}",
            total_amount=total
        )
        
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.price
        )
        
        # Reduce Stock
        product.stock -= quantity
        product.save()
        
        # Create Payment
        Payment.objects.create(
            order=order,
            amount=total,
            method=payment_method,
            is_successful=True
        )
        
        # Financial Transaction Journal Entry (10% commission, 90% seller)
        commission = total * Decimal('0.10')
        seller_share = total * Decimal('0.90')
        
        Transaction.objects.create(
            transaction_id=f"POS-{order.id:06d}",
            order=order,
            total_amount=total,
            payment_method=payment_method,
            platform_commission=commission,
            seller_amount=seller_share,
            delivery_fee=Decimal('0.00')
        )
        
        messages.success(request, f"Vente en magasin enregistrée avec succès ! Commande #{order.id} ({total} CFA).")
        return redirect('order_success', order_id=order.id)
        
    return render(request, 'frontend/pos.html', {'products': products})

def change_language(request, lang_code):
    if lang_code in ['fr', 'en']:
        request.session['site_lang'] = lang_code
    return redirect(request.META.get('HTTP_REFERER', '/'))
