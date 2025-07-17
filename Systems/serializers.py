from rest_framework import serializers
from .models import Category, Subcategory, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'slug']

class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug']

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'description', 'image', 'features', 'specifications', 'documentation', 'status', 'subcategory', 'slug']
        extra_kwargs = {
            'name': {'required': True},
            'price': {'required': True},
            'subcategory': {'required': True},
        }

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

    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None

    def validate(self, data):
        errors = {}
        for field in ['name', 'price', 'subcategory']:
            if not data.get(field):
                errors[field] = f"This field is required."
        if errors:
            raise serializers.ValidationError(errors)
        return data 