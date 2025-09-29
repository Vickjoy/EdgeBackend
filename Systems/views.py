from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.vary import vary_on_headers
from rest_framework import viewsets, status, serializers, generics, permissions
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2CallbackView
import logging

from .models import Category, Subcategory, Product
from .serializers import (
    CategorySerializer, SubcategorySerializer, ProductSerializer,
    UserRegistrationSerializer, UserProfileSerializer, CustomTokenObtainPairSerializer
)
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

# -------------------------
# Authentication Views
# -------------------------

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'access': str(access),
                'refresh': str(refresh)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        tokens = serializer.validated_data
        user = serializer.user
        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser
            },
            "access": tokens['access'],
            "refresh": tokens['refresh']
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

# -------------------------
# Social Login Callback
# -------------------------

class CustomGoogleOAuth2CallbackView(OAuth2CallbackView):
    """
    Custom Google OAuth callback that ensures proper redirect
    """
    adapter_class = GoogleOAuth2Adapter
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        if request.user.is_authenticated:
            next_url = request.session.get('socialaccount_next_url', '/')
            frontend_url = f"http://localhost:5173{next_url}"
            logger.debug(f"OAuth success, redirecting to: {frontend_url}")
            return HttpResponseRedirect(frontend_url)
        
        logger.debug("OAuth failed, redirecting to login")
        return HttpResponseRedirect("http://localhost:5173/user-login")

# -------------------------
# Cached ViewSets for your models
# -------------------------

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15-minute cache
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    pagination_class = None  

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        try:
            obj = get_object_or_404(queryset, **{self.lookup_field: self.kwargs[lookup_url_kwarg]})
            self.check_object_permissions(self.request, obj)
            return obj
        except Http404:
            raise serializers.ValidationError({"detail": "Category not found."})

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15-minute cache
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class SubcategoryViewSet(viewsets.ModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'slug'
    pagination_class = None  

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAdminUser()]

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

class DefaultPagination(PageNumberPagination):
    page_size = 40
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15-minute cache
@method_decorator(vary_on_headers('Authorization'), name='dispatch')
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]
    lookup_field = 'slug'
    pagination_class = DefaultPagination
    
    def get_permissions(self):
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return [IsAdminUser()]
        if self.action == 'list' and self.request.query_params.get('subcategory') is not None:
            return [IsAdminUser()]
        return [AllowAny()]

    def get_queryset(self):
        queryset = super().get_queryset()
        subcategory_slug = self.kwargs.get('subcategory_slug')
        subcategory_pk = self.kwargs.get('subcategory_pk')
        qp_subcat = self.request.query_params.get('subcategory')
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
        if qp_subcat:
            if str(qp_subcat).isdigit():
                return queryset.filter(subcategory__id=qp_subcat)
            return queryset.filter(subcategory__slug=qp_subcat)
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Http404:
            return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

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
        
        validated_data = serializer.validated_data
        if 'stock' not in validated_data:
            validated_data['stock'] = 1
        if 'status' not in validated_data:
            validated_data['status'] = Product.IN_STOCK
        serializer.save(subcategory=subcategory)

    def perform_update(self, serializer):
        instance = serializer.save()
        return instance

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

# -------------------------
# Admin-only PK-based views (no caching for write operations)
# -------------------------

class CategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'

class SubcategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubcategorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'pk'

    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        category = get_object_or_404(Category, slug=category_slug)
        return Subcategory.objects.filter(category=category)

class ProductAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

# -------------------------
# Legacy function-based views
# -------------------------

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

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    if email and User.objects.filter(email=email).exists():
        return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email or '', password=password)
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return Response({
        "access": str(access),
        "refresh": str(refresh)
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)
    if user is None:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    access = refresh.access_token

    return Response({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser
        },
        "access": str(access),
        "refresh": str(refresh)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    return Response({"message": "Logout successful"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    })

# -------------------------
# Social login success handler
# -------------------------

@login_required
def social_login_success(request):
    return redirect('http://localhost:5173/')

    def perform_update(self, serializer):
        instance = serializer.save()
        return instance

# -------------------------
# Public product endpoints with caching
# -------------------------

class ContractPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15-minute cache
class ProductsBySubcategoryView(generics.ListAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ContractPagination

    def get_queryset(self):
        return Product.objects.filter(subcategory__slug=self.kwargs.get('subcategory_slug')).order_by('-id')

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx

@method_decorator(cache_page(60 * 15), name='dispatch')  # 15-minute cache
class ProductDetailView(generics.RetrieveAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    lookup_url_kwarg = 'product_slug'
    queryset = Product.objects.all()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx