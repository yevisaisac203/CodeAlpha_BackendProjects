from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import MenuCategory, MenuItem, Table
from .serializers import (
    MenuCategorySerializer,
    MenuItemListSerializer,
    MenuItemDetailSerializer,
    MenuItemCreateSerializer,
    TableSerializer
)


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for MenuCategory
    - GET: Public access
    - POST, PUT, PATCH, DELETE: Admin only
    """
    queryset = MenuCategory.objects.all().order_by('display_order', 'name')
    serializer_class = MenuCategorySerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class MenuItemViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for MenuItem with advanced filtering and search
    - GET: Public access
    - POST, PUT, PATCH, DELETE: Admin only
    """
    queryset = MenuItem.objects.all().select_related('category')
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_available']
    search_fields = ['name', 'description', 'dietary_tags']
    ordering_fields = ['price', 'name', 'preparation_time_minutes']
    ordering = ['name']
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_availability']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'retrieve':
            return MenuItemDetailSerializer
        elif self.action == 'create':
            return MenuItemCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MenuItemCreateSerializer
        else:  # list, custom actions
            return MenuItemListSerializer
    
    @action(detail=True, methods=['patch'], url_path='availability')
    def toggle_availability(self, request, pk=None):
        """
        Toggle the is_available status of a menu item
        PATCH /api/menu-items/{id}/availability/
        """
        menu_item = self.get_object()
        menu_item.is_available = not menu_item.is_available
        menu_item.save()
        serializer = MenuItemDetailSerializer(menu_item)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='by-category')
    def by_category(self, request):
        """
        Get menu items grouped by category
        GET /api/menu-items/by-category/
        Returns: {category_name: [{item1}, {item2}, ...], ...}
        """
        items = MenuItem.objects.all().select_related('category')
        grouped_items = {}
        
        for item in items:
            category_name = item.category.name if item.category else 'Uncategorized'
            if category_name not in grouped_items:
                grouped_items[category_name] = []
            grouped_items[category_name].append(MenuItemListSerializer(item).data)
        
        return Response(grouped_items, status=status.HTTP_200_OK)


class TableViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Table management
    - GET: Public access
    - POST, PUT, PATCH, DELETE: Admin only
    """
    queryset = Table.objects.all().order_by('table_number')
    serializer_class = TableSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'location', 'capacity']
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """Override permissions based on action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'update_status']:
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        """
        Get available tables
        GET /api/tables/available/?capacity=4
        Optional query param: capacity (minimum capacity required)
        """
        tables = Table.objects.filter(status='available').order_by('table_number')
        
        # Optional capacity filter
        capacity = request.query_params.get('capacity')
        if capacity:
            try:
                capacity = int(capacity)
                tables = tables.filter(capacity__gte=capacity)
            except ValueError:
                return Response(
                    {'error': 'Capacity must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        serializer = TableSerializer(tables, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """
        Update table status
        PATCH /api/tables/{id}/status/
        Body: {"status": "occupied"}
        """
        table = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value:
            return Response(
                {'error': 'status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status choice
        valid_statuses = [choice[0] for choice in Table.STATUS_CHOICES]
        if status_value not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        table.status = status_value
        table.save()
        serializer = TableSerializer(table)
        return Response(serializer.data, status=status.HTTP_200_OK)
