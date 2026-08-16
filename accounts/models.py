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
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.role}"
