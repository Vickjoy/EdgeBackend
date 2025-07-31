from rest_framework import serializers
from .models import Category, Subcategory, Product, ProductSpecification

class CategorySerializer(serializers.ModelSerializer):
    # 'type' field is included and validated (choices: 'fire', 'ict')
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'slug']

class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']

class SubcategorySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'category']

class SubcategoryMiniSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer()
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'category']

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['key', 'value']

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    subcategory = serializers.PrimaryKeyRelatedField(queryset=Subcategory.objects.all(), required=True, write_only=True)
    subcategory_detail = SubcategoryMiniSerializer(source='subcategory', read_only=True)
    category = serializers.SerializerMethodField(read_only=True)
    specifications = ProductSpecificationSerializer(many=True)
    specifications_table = serializers.SerializerMethodField(read_only=True)
    subcategory_slug = serializers.SerializerMethodField()
    category_slug = serializers.SerializerMethodField()
    documentation_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'price', 'description', 'image', 'specifications',
            'specifications_table',
            'documentation', 'status', 'subcategory', 'subcategory_detail', 'category', 'slug'
        ]
        extra_kwargs = {
            'name': {'required': True},
            'price': {'required': False, 'allow_null': True},
            'description': {'required': False, 'allow_blank': True},
            'documentation': {'required': False, 'allow_blank': True},
        }

    def get_subcategory_slug(self, obj):
        return obj.subcategory.slug if obj.subcategory else None

    def get_category_slug(self, obj):
        return obj.subcategory.category.slug if obj.subcategory and obj.subcategory.category else None

    def get_documentation_url(self, obj):
        doc = obj.documentation
        request = self.context.get('request')
        if doc:
            # If it looks like a URL, return as is
            if doc.startswith('http://') or doc.startswith('https://'):
                return doc
            # If it looks like a file path, build full URL
            if request is not None:
                return request.build_absolute_uri('/media/' + doc.lstrip('/'))
            return '/media/' + doc.lstrip('/')
        return None

    def get_category(self, obj):
        if obj.subcategory and obj.subcategory.category:
            return CategoryMiniSerializer(obj.subcategory.category).data
        return None

    def get_specifications_table(self, obj):
        return obj.get_specifications_table() if hasattr(obj, 'get_specifications_table') else []

    def to_internal_value(self, data):
        subcategory_value = data.get('subcategory')
        if subcategory_value and not str(subcategory_value).isdigit():
            try:
                subcategory = Subcategory.objects.get(slug=subcategory_value)
                data = data.copy()
                data['subcategory'] = subcategory.id
            except Subcategory.DoesNotExist:
                raise serializers.ValidationError({'subcategory': 'Subcategory not found.'})
        return super().to_internal_value(data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        image_field = getattr(instance, 'image', None)
        if image_field and getattr(image_field, 'url', None):
            url = image_field.url
            if request is not None:
                rep['image'] = request.build_absolute_uri(url)
            else:
                rep['image'] = url
        else:
            rep['image'] = None
        # Handle missing or empty price values
        if rep.get('price') in [None, '']:
            rep['price'] = None
        return rep

    def validate(self, data):
        errors = {}
        if not data.get('name'):
            errors['name'] = "This field is required."
        # price is now optional, so no validation error if missing
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        specifications_data = validated_data.pop('specifications', [])
        product = Product.objects.create(**validated_data)
        for spec in specifications_data:
            ProductSpecification.objects.create(product=product, **spec)
        return product

    def update(self, instance, validated_data):
        specifications_data = validated_data.pop('specifications', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if specifications_data is not None:
            instance.specifications.all().delete()
            for spec in specifications_data:
                ProductSpecification.objects.create(product=instance, **spec)
        return instance 