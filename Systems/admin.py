from django.contrib import admin
from .models import Category, Subcategory, Product

class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1

class ProductInline(admin.TabularInline):
    model = Product
    extra = 1

class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubcategoryInline]
    list_display = ('name',)

class SubcategoryAdmin(admin.ModelAdmin):
    inlines = [ProductInline]
    list_display = ('name', 'category')
    list_filter = ('category',)

admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Product)
