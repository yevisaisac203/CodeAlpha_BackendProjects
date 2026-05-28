from rest_framework import serializers
from .models import MenuCategory, MenuItem, Table


class MenuCategorySerializer(serializers.ModelSerializer):
    """Serializer for MenuCategory model"""
    class Meta:
        model = MenuCategory
        fields = '__all__'


class MenuItemListSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem list view"""
    category = MenuCategorySerializer(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'category', 'price', 'image',
            'is_available', 'preparation_time_minutes', 'dietary_tags'
        ]


class MenuItemDetailSerializer(serializers.ModelSerializer):
    """Serializer for MenuItem detail view - extends list with more fields"""
    category = MenuCategorySerializer(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'category', 'description', 'price', 'image',
            'is_available', 'preparation_time_minutes', 'calories',
            'dietary_tags', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating MenuItem"""
    class Meta:
        model = MenuItem
        fields = [
            'name', 'description', 'category', 'price', 'image',
            'is_available', 'preparation_time_minutes', 'calories', 'dietary_tags'
        ]
    
    def validate_price(self, value):
        """Validate that price is greater than 0"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value


class TableSerializer(serializers.ModelSerializer):
    """Serializer for Table model"""
    qr_code_token = serializers.UUIDField(read_only=True)
    
    class Meta:
        model = Table
        fields = '__all__'
        read_only_fields = ['qr_code_token']
