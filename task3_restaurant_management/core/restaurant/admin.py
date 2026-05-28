from django.contrib import admin
from .models import (
    MenuCategory, MenuItem, Table, Reservation, 
    Order, OrderItem, InventoryItem
)


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('display_order', 'name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available', 'preparation_time_minutes')
    list_filter = ('category', 'is_available', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'description', 'category', 'price')
        }),
        ('Image & Availability', {
            'fields': ('image', 'is_available')
        }),
        ('Additional Info', {
            'fields': ('preparation_time_minutes', 'calories', 'dietary_tags')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('table_number', 'capacity', 'location', 'status')
    list_filter = ('location', 'status')
    search_fields = ('table_number',)
    readonly_fields = ('qr_code_token',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'customer_phone', 'reservation_datetime', 'party_size', 'status')
    list_filter = ('status', 'reservation_datetime', 'created_at')
    search_fields = ('customer_name', 'customer_phone', 'customer_email')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Customer Info', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Reservation Details', {
            'fields': ('table', 'reservation_datetime', 'party_size', 'status')
        }),
        ('Special Requests', {
            'fields': ('special_requests',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('order',)
    fields = ('menu_item', 'quantity', 'unit_price', 'special_instructions', 'status')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'order_type', 'status', 'total_amount', 'payment_method', 'created_at')
    list_filter = ('status', 'order_type', 'payment_method', 'created_at')
    search_fields = ('order_number', 'customer_name')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    fieldsets = (
        ('Order Info', {
            'fields': ('order_number', 'order_type', 'status')
        }),
        ('Related', {
            'fields': ('table', 'reservation')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'total_amount')
        }),
        ('Payment & Delivery', {
            'fields': ('payment_method', 'customer_name', 'delivery_address')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['recalculate_totals_action']
    
    def recalculate_totals_action(self, request, queryset):
        """Action to recalculate totals for selected orders"""
        for order in queryset:
            order.recalculate_totals()
        self.message_user(request, f'Recalculated totals for {queryset.count()} orders.')
    
    recalculate_totals_action.short_description = 'Recalculate totals for selected orders'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'unit_price', 'status')
    list_filter = ('status', 'order__created_at')
    search_fields = ('order__order_number', 'menu_item__name')
    readonly_fields = ('order',)


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'current_stock', 'minimum_stock_alert', 'is_low_stock', 'supplier_name')
    list_filter = ('unit', 'supplier_name')
    search_fields = ('name', 'supplier_name')
    readonly_fields = ('last_restocked_at',)
    fieldsets = (
        ('Item Info', {
            'fields': ('name', 'unit')
        }),
        ('Stock Levels', {
            'fields': ('current_stock', 'minimum_stock_alert', 'is_low_stock')
        }),
        ('Supplier & Cost', {
            'fields': ('supplier_name', 'unit_cost')
        }),
        ('Timestamps', {
            'fields': ('last_restocked_at',),
            'classes': ('collapse',)
        }),
    )
    
    def is_low_stock(self, obj):
        """Display low stock status"""
        return obj.is_low_stock
    
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock Alert'
