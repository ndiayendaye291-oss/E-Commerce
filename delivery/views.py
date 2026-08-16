from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Delivery
from .serializers import DeliverySerializer

class DeliveryViewSet(viewsets.ModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return Delivery.objects.all()
        elif user.role == 'DELIVERY':
            return Delivery.objects.filter(delivery_person=user)
        return Delivery.objects.filter(order__user=user)
