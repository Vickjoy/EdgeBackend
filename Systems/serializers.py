from rest_framework import serializers
from .models import Category, Subcategory, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'type', 'slug']

class SubcategorySerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Subcategory
        fields = ['id', 'name', 'slug', 'category']

class ProductSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

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

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        image_field = getattr(instance, 'image', None)
        if image_field and image_field.name:
            url = image_field.url
            if request is not None:
                rep['image'] = request.build_absolute_uri(url)
            else:
                rep['image'] = url
        else:
            rep['image'] = None
        return rep

    def validate(self, data):
        errors = {}
        for field in ['name', 'price', 'subcategory']:
            if not data.get(field):
                errors[field] = f"This field is required."
        if errors:
            raise serializers.ValidationError(errors)
        return data 