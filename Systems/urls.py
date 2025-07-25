from rest_framework_nested import routers
from .views import CategoryViewSet, SubcategoryViewSet, ProductViewSet, me_view
from django.urls import path

router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
# router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')  # Removed global subcategories endpoint
router.register(r'products', ProductViewSet, basename='product')

# Nested router for subcategories under categories
categories_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
categories_router.register(r'subcategories', SubcategoryViewSet, basename='category-subcategories')

# Removed nested router for products under subcategories
# subcategories_router = routers.NestedDefaultRouter(router, r'subcategories', lookup='subcategory')
# subcategories_router.register(r'products', ProductViewSet, basename='subcategory-products')

urlpatterns = router.urls + categories_router.urls  # Removed subcategories_router.urls
urlpatterns += [
    path('me/', me_view, name='me'),
    path('categories/<slug:category_slug>/subcategories/', SubcategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='subcategory-by-category-slug'),
    path('categories/<slug:category_slug>/subcategories/<int:pk>/', SubcategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='subcategory-detail-by-category'),
    path('subcategories/<slug:subcategory_slug>/products/', ProductViewSet.as_view({'get': 'list', 'post': 'create'}), name='product-by-subcategory-slug'),
] 