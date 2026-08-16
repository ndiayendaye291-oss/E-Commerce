from django.db import models
from django.conf import settings
from orders.models import Order

class Delivery(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'En attente d\'assignation'),
        ('ASSIGNED', 'Assignée au livreur'),
        ('IN_TRANSIT', 'En cours de livraison'),
        ('DELIVERED', 'Livrée'),
    )
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery')
    delivery_person = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'DELIVERY'},
        related_name='deliveries'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Livraison pour Commande #{self.order.id} - Statut: {self.get_status_display()}"
