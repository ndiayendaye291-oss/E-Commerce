from django.shortcuts import render
from catalog.models import Product, Category

def index(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    context = {
        'products': products,
        'categories': categories,
    }
    return render(request, 'frontend/index.html', context)
