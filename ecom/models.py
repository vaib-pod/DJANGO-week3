from django.db import models
from django.contrib.auth.models import User 

class Tag(models.Model):
    name = models.CharField(max_length=50 , unique=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=300)
    date_added = models.DateField(auto_now_add=True)
    date_updated = models.DateField(auto_now=True)
    image = models.ImageField(upload_to='products/')
    stock = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.ManyToManyField(Tag, blank=True, related_name="products")
        
    def __str__(self):
        return f'{self.name}' 
    
class Order(models.Model):
    user = models.ForeignKey(User , on_delete=models.SET_NULL, null=True , blank= True)
    total_amount = models.DecimalField( max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class Cart(models.Model):
    user = models.ForeignKey(User , on_delete=models.CASCADE, null=True , blank= True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()