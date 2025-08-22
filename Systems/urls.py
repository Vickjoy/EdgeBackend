from rest_framework_nested import routers
from .views import (
    CategoryViewSet, SubcategoryViewSet, ProductViewSet,
    me_view, register_view, login_view, logout_view, current_user_view,
    CategoryAdminDetailView, SubcategoryAdminDetailView, ProductAdminDetailView,
    ProductDetailView
)
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

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

    # (legacy) custom API auth endpoints not used by frontend but kept for compatibility
    # path('auth/logout/', logout_view, name='custom_api_logout'),
    # path('auth/user/', current_user_view, name='current_user'),

    # Slug-based endpoints for public product and nested browsing
    # removed overlapping slug route to honor /products/<slug:product_slug>/

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

    # JWT endpoints (added)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # --- Contract-specific endpoints ---
    # Auth endpoints (SimpleJWT)
    path('auth/register/', register_view),  # returns tokens on 201
    path('auth/login/', login_view),        # returns access/refresh
    path('me/', me_view),                   # returns user data

    # Product endpoints
    path('subcategories/<slug:subcategory_slug>/products/',
         ProductViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('products/<slug:product_slug>/', ProductDetailView.as_view(), name='product-detail-contract'),

    # Admin-only endpoints (pk based updates/deletes)
    path('categories/<int:pk>/', CategoryAdminDetailView.as_view()),
    path('categories/<slug:category_slug>/subcategories/<int:pk>/', SubcategoryAdminDetailView.as_view()),
    path('products/<int:pk>/', ProductAdminDetailView.as_view()),
]
