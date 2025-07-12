from django.contrib import admin
from .models import *


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'date_added']
    list_filter = ['date_added', 'tags']
    search_fields = ['name', 'description']
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at']

class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(OrderItem,OrderItemAdmin)
admin.site.register(Tag,TagAdmin)




