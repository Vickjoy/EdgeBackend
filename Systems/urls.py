from rest_framework_nested import routers
from .views import (
    CategoryViewSet, SubcategoryViewSet, ProductViewSet, 
    me_view, register_view, login_view, logout_view, current_user_view
)
from django.urls import path, include

# Main router
router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'products', ProductViewSet, basename='product')

# Nested routers
categories_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
categories_router.register(r'subcategories', SubcategoryViewSet, basename='category-subcategories')

subcategories_router = routers.NestedDefaultRouter(router, r'subcategories', lookup='subcategory')
subcategories_router.register(r'products', ProductViewSet, basename='subcategory-products')

urlpatterns = [
    # Routers
    path('', include(router.urls)),
    path('', include(categories_router.urls)),
    path('', include(subcategories_router.urls)),

    # 🔑 Custom API authentication endpoints (JSON-based)
    path('auth/register/', register_view, name='api_register'),
    path('auth/login/', login_view, name='custom_api_login'),   # renamed
    path('auth/logout/', logout_view, name='custom_api_logout'), # renamed
    path('auth/user/', current_user_view, name='current_user'),

    # Me endpoint
    path('me/', me_view, name='me'),

    # Slug-based endpoints
    path('products/<slug:slug>/',
         ProductViewSet.as_view({'get': 'retrieve'}),
         name='product-detail-direct'),

    path('categories/<slug:category_slug>/subcategories/',
         SubcategoryViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='subcategory-by-category-slug'),

    path('categories/<slug:category_slug>/subcategories/<slug:slug>/',
         SubcategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='subcategory-detail-by-slug'),

    path('subcategories/<slug:subcategory_slug>/products/',
         ProductViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='product-by-subcategory-slug'),

    path('subcategories/<slug:subcategory_slug>/products/<slug:slug>/',
         ProductViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='product-detail-by-slug'),
]
