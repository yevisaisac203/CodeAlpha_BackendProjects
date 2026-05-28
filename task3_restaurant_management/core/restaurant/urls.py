from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuCategoryViewSet, MenuItemViewSet, TableViewSet

router = DefaultRouter()
router.register(r'categories', MenuCategoryViewSet, basename='menucategory')
router.register(r'menu-items', MenuItemViewSet, basename='menuitem')
router.register(r'tables', TableViewSet, basename='table')

urlpatterns = [
    path('', include(router.urls)),
]
