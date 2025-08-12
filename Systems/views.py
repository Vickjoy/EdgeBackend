from django.http import Http404
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import Category, Subcategory, Product
from .serializers import CategorySerializer, SubcategorySerializer, ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        
        try:
            obj = get_object_or_404(queryset, **{self.lookup_field: self.kwargs[lookup_url_kwarg]})
            self.check_object_permissions(self.request, obj)
            return obj
        except Http404:
            raise serializers.ValidationError({"detail": "Category not found."})

class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.kwargs.get('category_slug')
        
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            return queryset.filter(category=category)
        return queryset

    def perform_create(self, serializer):
        category_slug = self.kwargs.get('category_slug')
        category_id = self.kwargs.get('category_pk')
        
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
        elif category_id:
            try:
                if str(category_id).isdigit():
                    category = get_object_or_404(Category, id=category_id)
                else:
                    category = get_object_or_404(Category, slug=category_id)
            except ValueError:
                raise serializers.ValidationError({"detail": "Invalid category ID."})
        else:
            raise serializers.ValidationError({"detail": "Category not specified."})
        
        serializer.save(category=category)

    def get_object(self):
        try:
            return super().get_object()
        except Http404:
            raise serializers.ValidationError({"detail": "Subcategory not found."})

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        subcategory_slug = self.kwargs.get('subcategory_slug')
        subcategory_pk = self.kwargs.get('subcategory_pk')
        
        if subcategory_slug:
            subcategory = get_object_or_404(Subcategory, slug=subcategory_slug)
            return queryset.filter(subcategory=subcategory)
        
        if subcategory_pk:
            try:
                if str(subcategory_pk).isdigit():
                    subcategory = get_object_or_404(Subcategory, id=subcategory_pk)
                else:
                    subcategory = get_object_or_404(Subcategory, slug=subcategory_pk)
            except ValueError:
                raise serializers.ValidationError({"detail": "Invalid subcategory ID."})
            return queryset.filter(subcategory=subcategory)
        
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

    def perform_create(self, serializer):
        subcategory_slug = self.kwargs.get('subcategory_slug')
        subcategory_pk = self.kwargs.get('subcategory_pk')
        
        if subcategory_slug:
            subcategory = get_object_or_404(Subcategory, slug=subcategory_slug)
        elif subcategory_pk:
            try:
                if str(subcategory_pk).isdigit():
                    subcategory = get_object_or_404(Subcategory, id=subcategory_pk)
                else:
                    subcategory = get_object_or_404(Subcategory, slug=subcategory_pk)
            except ValueError:
                raise serializers.ValidationError({"detail": "Invalid subcategory ID."})
        else:
            raise serializers.ValidationError({"detail": "Subcategory not specified."})
        
        serializer.save(subcategory=subcategory)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=False, methods=['get'])
    def all_categories(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def all_subcategories(self, request):
        subcategories = Subcategory.objects.all()
        serializer = SubcategorySerializer(subcategories, many=True, context={'request': request})
        return Response(serializer.data)

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