from django.contrib import admin
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Category, Subcategory, Product, SpecificationTable, SpecificationRow


# Inlines for nested specifications
class SpecificationRowInline(admin.TabularInline):
    model = SpecificationRow
    extra = 1


class SpecificationTableInline(admin.StackedInline):
    model = SpecificationTable
    extra = 1
    show_change_link = True
    inlines = [SpecificationRowInline]


class SubcategoryInline(admin.TabularInline):
    model = Subcategory
    extra = 1


class ProductInline(admin.TabularInline):
    model = Product
    extra = 1


# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubcategoryInline]
    list_display = ('name', 'slug')
    readonly_fields = ('slug',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('slug',)
        return self.readonly_fields


# Subcategory Admin
class SubcategoryAdmin(admin.ModelAdmin):
    inlines = [ProductInline]
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    readonly_fields = ('slug',)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('slug',)
        return self.readonly_fields


# Import-export resource for products
class ProductResource(resources.ModelResource):
    category = fields.Field(column_name='category')
    subcategory = fields.Field(column_name='subcategory')

    class Meta:
        model = Product
        import_id_fields = ['slug']
        fields = (
            'name', 'price', 'description', 'documentation', 'documentation_label',
            'status', 'image', 'slug', 'subcategory', 'category'
        )
        skip_unchanged = True
        report_skipped = True

    def before_import_row(self, row, **kwargs):
        category_name = row.get('category')
        subcategory_name = row.get('subcategory')
        try:
            category = Category.objects.get(name=category_name)
            subcategory = Subcategory.objects.get(name=subcategory_name, category=category)
            row['subcategory'] = subcategory.pk
        except Category.DoesNotExist:
            raise Exception(f"Category '{category_name}' does not exist.")
        except Subcategory.DoesNotExist:
            raise Exception(f"Subcategory '{subcategory_name}' under '{category_name}' not found.")


# Product Admin
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    inlines = [SpecificationTableInline]
    list_display = ('name', 'subcategory', 'get_category', 'price', 'status', 'image_preview', 'documentation_preview')
    readonly_fields = ('get_category', 'image_preview', 'slug')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subcategory', 'price', 'status', 'stock')
        }),
        ('Content', {
            'fields': ('description', 'features', 'image')
        }),
        ('Documentation', {
            'fields': ('documentation', 'documentation_label'),
            'description': 'Enter the URL for the product datasheet and the text to display for the link.'
        }),
    )

    def get_category(self, obj):
        return obj.subcategory.category if obj.subcategory else None
    get_category.short_description = 'Category'
    
    def image_preview(self, obj):
        if obj.image:
            try:
                # Force the image URL to use Cloudinary if it's not already
                image_url = str(obj.image.url) if hasattr(obj.image, 'url') else str(obj.image)
                if not image_url.startswith('http'):
                    image_url = f'https://res.cloudinary.com/ddwpy1x3v/{image_url}'
                return mark_safe(f'<img src="{image_url}" style="width: 50px; height: 50px; object-fit: cover;" />')
            except:
                return "Image Error"
        return "No Image"
    image_preview.short_description = 'Image Preview'
    
    def documentation_preview(self, obj):
        if obj.documentation:
            label = obj.documentation_label or 'View Documentation'
            return mark_safe(f'<a href="{obj.documentation}" target="_blank">{label}</a>')
        return "No Documentation"
    documentation_preview.short_description = 'Documentation'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('slug',)
        return self.readonly_fields


# Register models
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(SpecificationTable)
admin.site.register(SpecificationRow)