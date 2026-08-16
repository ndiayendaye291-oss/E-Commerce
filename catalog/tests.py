from django.test import TestCase
from .models import Category, Product

class CatalogTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Electronics', description='Tech stuff')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            description='A nice laptop',
            price=1000.00,
            stock=10
        )
        
    def test_category_creation(self):
        self.assertEqual(self.category.name, 'Electronics')
        self.assertEqual(str(self.category), 'Electronics')
        
    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Laptop')
        self.assertEqual(self.product.price, 1000.00)
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(self.product.category, self.category)
