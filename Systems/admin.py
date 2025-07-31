from django.contrib import admin
from .models import Category, Subcategory, Product, ProductSpecification

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubcategoryInline]
    list_display = ('name',)

class SubcategoryAdmin(admin.ModelAdmin):
    inlines = [ProductInline]
    list_display = ('name', 'category')
    list_filter = ('category',)

# Optionally, keep ProductAdmin for direct product editing
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductSpecificationInline]
    list_display = ('name', 'subcategory', 'category', 'price', 'status')
    readonly_fields = ('category',)

    def category(self, obj):
        return obj.subcategory.category if obj.subcategory else None
    category.short_description = 'Category'

admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductSpecification)
