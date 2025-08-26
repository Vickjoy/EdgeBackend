from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import Category, Subcategory, Product, SpecificationTable, SpecificationRow
import os
from decimal import Decimal

# -- USER AUTHENTICATION SERIALIZERS --
class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'first_name', 'last_name')
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
        
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'date_joined')
        read_only_fields = ('id', 'is_staff', 'is_superuser', 'date_joined')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'username'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow login with either username or email
        self.fields['username'] = serializers.CharField()
        self.fields['password'] = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        # Try to find user by username first, then by email
        user = None
        if '@' in username:
            # Looks like an email
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass
        
        # Use the original validation with username
        attrs['username'] = username
        return super().validate(attrs)

# -- SUBCATEGORY MINI SERIALIZER --
class SubcategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug']

# -- CATEGORY SERIALIZERS --
class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategoryMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'slug', 'subcategories']

class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

# -- SUBCATEGORY SERIALIZERS --
class SubcategorySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'category']

# -- SPECIFICATION SERIALIZERS --
class SpecificationRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationRow
        fields = ['key', 'value']

class SpecificationTableSerializer(serializers.ModelSerializer):
    rows = SpecificationRowSerializer(many=True, read_only=True)

    class Meta:
        model = SpecificationTable
        fields = ['title', 'rows']

# -- PRODUCT SERIALIZER --
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    price_requires_login = serializers.SerializerMethodField()
    subcategory = serializers.PrimaryKeyRelatedField(
        queryset=Subcategory.objects.all(),
        required=True,
        write_only=True
    )
    subcategory_detail = SubcategoryMiniSerializer(source='subcategory', read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    spec_tables = SpecificationTableSerializer(many=True, read_only=True)
    subcategory_slug = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    documentation_url = serializers.SerializerMethodField()
    documentation_label = serializers.SerializerMethodField()
    features = serializers.CharField(required=False, allow_blank=True)

    CLOUDINARY_BASE_URL = 'https://res.cloudinary.com/ddwpy1x3v/'

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'price_visibility', 'price_requires_login',
            'description', 'features', 'image',
            'spec_tables', 'documentation', 'documentation_url', 'documentation_label',
            'status', 'subcategory', 'subcategory_detail',
            'category', 'slug', 'subcategory_slug', 'category_slug'
        ]

    # -- PRICE VISIBILITY LOGIC --
    def get_price(self, obj):
        # Respect per-product price visibility
        request = self.context.get('request')
        user_is_auth = bool(request and getattr(request, 'user', None) and request.user.is_authenticated)
        if obj.price_visibility == Product.LOGIN_REQUIRED and not user_is_auth:
            return None
        return float(obj.price) if obj.price is not None else 0.00

    def get_price_requires_login(self, obj):
        # Return True if price requires login and user is not authenticated
        request = self.context.get('request')
        
        # True only when this product requires login and user is not authenticated
        user_is_auth = bool(request and getattr(request, 'user', None) and request.user.is_authenticated)
        if obj.price_visibility == Product.LOGIN_REQUIRED and not user_is_auth:
            return True
        
        return False

    # -- IMAGE URL FIX --
    def get_image(self, obj):
        if obj.image:
            url = str(obj.image)
            # If already full URL, return as-is
            if url.startswith('http://') or url.startswith('https://'):
                return url
            # Otherwise prepend Cloudinary base URL
            return self.CLOUDINARY_BASE_URL + url
        return None

    def get_subcategory_slug(self, obj):
        return obj.subcategory.slug if obj.subcategory else None

    def get_category_slug(self, obj):
        return obj.subcategory.category.slug if obj.subcategory and obj.subcategory.category else None

    def get_documentation_url(self, obj):
        # Return the URL directly since it's now stored as a URL field
        return obj.documentation if obj.documentation else None

    def get_documentation_label(self, obj):
        # Return the custom label or extract filename from URL
        if obj.documentation:
            if obj.documentation_label:
                return obj.documentation_label
            else:
                # Extract filename from URL keeping the original format
                import re
                from urllib.parse import urlparse
                try:
                    # Parse the URL to get the path
                    parsed_url = urlparse(obj.documentation)
                    filename = os.path.basename(parsed_url.path)
                    # Remove file extension but keep original formatting
                    filename_without_ext = os.path.splitext(filename)[0]
                    # Return the filename as-is (with hyphens, etc.)
                    if filename_without_ext.strip():
                        return filename_without_ext
                    else:
                        return "View Documentation"
                except:
                    return "View Documentation"
        return None

    def get_category(self, obj):
        if obj.subcategory and obj.subcategory.category:
            return CategoryMiniSerializer(obj.subcategory.category).data
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Normalize status for frontend: in_stock | out_of_stock
        try:
            stock = getattr(instance, 'stock', 0)
            data['status'] = 'in_stock' if stock and stock > 0 else 'out_of_stock'
        except Exception:
            pass
        return data