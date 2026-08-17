from django import forms
from django.contrib.auth.forms import UserCreationForm
from accounts.models import CustomUser
from catalog.models import Product

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'role', 'phone_number', 'address')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'category', 'price', 'stock', 'description', 'image')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class AdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username', 'email', 'phone_number',
            'can_manage_orders', 'can_manage_payments', 
            'can_manage_sellers', 'can_manage_deliverers', 
            'can_view_analytics'
        )
        labels = {
            'can_manage_orders': 'Gérer les commandes',
            'can_manage_payments': 'Gérer les paiements',
            'can_manage_sellers': 'Gérer les vendeurs',
            'can_manage_deliverers': 'Gérer les livreurs',
            'can_view_analytics': 'Voir les rapports financiers',
        }
