from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Category, Subcategory, Product
from .serializers import CategorySerializer, SubcategorySerializer, ProductSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import Http404
from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, FormParser

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            return Subcategory.objects.filter(category__slug=category_slug)
        return Subcategory.objects.all()

    def perform_create(self, serializer):
        category_slug = self.kwargs.get('category_slug')
        category_id = self.kwargs.get('category_pk')
        category = None
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Category not found")
        elif category_id:
            try:
                if str(category_id).isdigit():
                    category = Category.objects.get(id=category_id)
                else:
                    category = Category.objects.get(slug=category_id)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Category not found")
        if category is not None:
            serializer.save(category=category)
        else:
            raise serializers.ValidationError("Category not found in URL.")

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Prefer explicit slug
        subcategory_slug = self.kwargs.get('subcategory_slug')
        if subcategory_slug:
            try:
                subcategory = Subcategory.objects.get(slug=subcategory_slug)
            except Subcategory.DoesNotExist:
                raise Http404("Subcategory not found")
            return Product.objects.filter(subcategory_id=subcategory.id)
        # Handle nested router case where subcategory_pk may be a slug or an ID
        subcategory_pk = self.kwargs.get('subcategory_pk')
        if subcategory_pk:
            try:
                if str(subcategory_pk).isdigit():
                    subcategory = Subcategory.objects.get(id=subcategory_pk)
                else:
                    subcategory = Subcategory.objects.get(slug=subcategory_pk)
            except Subcategory.DoesNotExist:
                raise Http404("Subcategory not found")
            return Product.objects.filter(subcategory_id=subcategory.id)
        return Product.objects.all()

    def perform_create(self, serializer):
        subcategory_slug = self.kwargs.get('subcategory_slug')
        subcategory_id = self.kwargs.get('subcategory_pk')
        subcategory = None
        # Prefer explicit slug
        if subcategory_slug:
            try:
                subcategory = Subcategory.objects.get(slug=subcategory_slug)
            except Subcategory.DoesNotExist:
                raise serializers.ValidationError("Subcategory not found")
        # If subcategory_pk is present, check if it's numeric (ID) or a slug
        elif subcategory_id:
            try:
                if str(subcategory_id).isdigit():
                    subcategory = Subcategory.objects.get(id=subcategory_id)
                else:
                    subcategory = Subcategory.objects.get(slug=subcategory_id)
            except Subcategory.DoesNotExist:
                raise serializers.ValidationError("Subcategory not found")
        if subcategory is not None:
            serializer.save(subcategory=subcategory)
        else:
            raise serializers.ValidationError("Subcategory not found in URL.")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    })
