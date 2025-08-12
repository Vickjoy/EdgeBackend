from rest_framework import serializers
from .models import Category, Subcategory, Product, SpecificationTable, SpecificationRow
import os
from decimal import Decimal


# --- SUBCATEGORY MINI SERIALIZER ---
class SubcategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug']


# --- CATEGORY SERIALIZERS ---
class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategoryMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'slug', 'subcategories']


class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# --- SUBCATEGORY SERIALIZERS ---
class SubcategorySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'category']


# --- SPECIFICATION SERIALIZERS ---
class SpecificationRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationRow
        fields = ['key', 'value']


class SpecificationTableSerializer(serializers.ModelSerializer):
    rows = SpecificationRowSerializer(many=True, read_only=True)

    class Meta:
        model = SpecificationTable
        fields = ['title', 'rows']


# --- PRODUCT SERIALIZER ---
class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
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
            'id', 'name', 'price', 'description', 'features', 'image',
            'spec_tables', 'documentation', 'documentation_url', 'documentation_label',
            'status', 'subcategory', 'subcategory_detail',
            'category', 'slug', 'subcategory_slug', 'category_slug'
        ]

    # --- PRICE FIX ---
    def get_price(self, obj):
        return float(obj.price) if obj.price is not None else 0.00

    # --- IMAGE URL FIX ---
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