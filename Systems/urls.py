from rest_framework_nested import routers
from .views import CategoryViewSet, SubcategoryViewSet, ProductViewSet, me_view
from django.urls import path

router = routers.DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubcategoryViewSet, basename='subcategory')
router.register(r'products', ProductViewSet, basename='product')

# Nested router for subcategories under categories
categories_router = routers.NestedDefaultRouter(router, r'categories', lookup='category')
categories_router.register(r'subcategories', SubcategoryViewSet, basename='category-subcategories')

# Nested router for products under subcategories
subcategories_router = routers.NestedDefaultRouter(router, r'subcategories', lookup='subcategory')
subcategories_router.register(r'products', ProductViewSet, basename='subcategory-products')

urlpatterns = router.urls + categories_router.urls + subcategories_router.urls
urlpatterns += [
    path('me/', me_view, name='me'),
    path('categories/<slug:category_slug>/subcategories/', SubcategoryViewSet.as_view({'get': 'list'}), name='subcategory-by-category-slug'),
    path('subcategories/<slug:subcategory_slug>/products/', ProductViewSet.as_view({'get': 'list'}), name='product-by-subcategory-slug'),
] 