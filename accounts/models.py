from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('CLIENT', 'Client'),
        ('SELLER', 'Vendeur'),
        ('ADMIN', 'Administrateur'),
        ('DELIVERY', 'Livreur'),
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='CLIENT')
    role_request = models.CharField(max_length=15, choices=ROLE_CHOICES, blank=True, null=True)
    role_request_rejected = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True, help_text="Permet aux Vendeurs/Livreurs d'accéder à leurs espaces.")
    is_blocked = models.BooleanField(default=False, help_text="Permet d'interdire l'accès à un utilisateur suspendu par le Superadmin.")
    
    # Granular Permissions for Secondary Admins
    can_manage_orders = models.BooleanField(default=True)
    can_manage_payments = models.BooleanField(default=True)
    can_manage_sellers = models.BooleanField(default=True)
    can_manage_deliverers = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)

    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.role}"
