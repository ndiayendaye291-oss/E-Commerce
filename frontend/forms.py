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
