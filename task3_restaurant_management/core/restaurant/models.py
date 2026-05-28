import uuid
from django.db import models
from django.utils import timezone
from decimal import Decimal


class MenuCategory(models.Model):
    """Restaurant menu category"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class MenuItem(models.Model):
    """Individual menu item"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(MenuCategory, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='menu/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    preparation_time_minutes = models.PositiveIntegerField(default=15)
    calories = models.PositiveIntegerField(null=True, blank=True)
    dietary_tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags (e.g., vegan,gluten-free)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category.name if self.category else 'Uncategorized'})"


class Table(models.Model):
    """Restaurant table"""
    LOCATION_CHOICES = [
        ('indoor', 'Indoor'),
        ('outdoor', 'Outdoor'),
        ('bar', 'Bar'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Maintenance'),
    ]
    
    table_number = models.PositiveIntegerField(unique=True)
    capacity = models.PositiveIntegerField()
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, default='indoor')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    qr_code_token = models.UUIDField(default=uuid.uuid4, editable=False)
    
    class Meta:
        ordering = ['table_number']
    
    def __str__(self):
        return f"Table {self.table_number} (Capacity: {self.capacity})"


class Reservation(models.Model):
    """Table reservation"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('seated', 'Seated'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ]
    
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField()
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    reservation_datetime = models.DateTimeField()
    party_size = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    special_requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-reservation_datetime']
    
    def __str__(self):
        return f"Reservation for {self.customer_name} on {self.reservation_datetime.strftime('%Y-%m-%d %H:%M')}"


class Order(models.Model):
    """Restaurant order"""
    ORDER_TYPE_CHOICES = [
        ('dine_in', 'Dine In'),
        ('takeaway', 'Takeaway'),
        ('delivery', 'Delivery'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
        ('unpaid', 'Unpaid'),
    ]
    
    order_number = models.CharField(max_length=30, unique=True, editable=False)
    table = models.ForeignKey(Table, on_delete=models.SET_NULL, null=True, blank=True)
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True)
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='dine_in')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='unpaid')
    customer_name = models.CharField(max_length=200, blank=True)
    delivery_address = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """Generate order number on first save"""
        if not self.order_number:
            today = timezone.now().strftime('%Y%m%d')
            today_orders = Order.objects.filter(
                order_number__startswith=f'ORD-{today}'
            ).count()
            sequence = str(today_orders + 1).zfill(4)
            self.order_number = f'ORD-{today}-{sequence}'
        super().save(*args, **kwargs)
    
    def recalculate_totals(self):
        """Recalculate order totals based on order items"""
        self.subtotal = sum(
            item.unit_price * item.quantity 
            for item in self.items.all()
        ) or Decimal('0.00')
        self.tax_amount = self.subtotal * Decimal('0.16')
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save()
    
    def __str__(self):
        return f"Order {self.order_number} - {self.get_status_display()}"


class OrderItem(models.Model):
    """Individual item in an order"""
    ITEM_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('served', 'Served'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price snapshot at order time")
    special_instructions = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='pending')
    
    class Meta:
        ordering = ['order', 'menu_item']
    
    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity} (Order {self.order.order_number})"


class InventoryItem(models.Model):
    """Inventory/Stock management"""
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('g', 'Gram'),
        ('L', 'Liter'),
        ('ml', 'Milliliter'),
        ('units', 'Units'),
        ('pieces', 'Pieces'),
    ]
    
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    current_stock = models.DecimalField(max_digits=10, decimal_places=3)
    minimum_stock_alert = models.DecimalField(max_digits=10, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    supplier_name = models.CharField(max_length=200, blank=True)
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['name']
    
    @property
    def is_low_stock(self):
        """Check if current stock is at or below minimum alert level"""
        return self.current_stock <= self.minimum_stock_alert
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"
