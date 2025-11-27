from django.contrib import admin
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Category, Subcategory, Product, SpecificationTable, SpecificationRow, Blog
from allauth.socialaccount.models import SocialApp

admin.site.unregister(SocialApp)

# Register your custom admin
@admin.register(SocialApp)
class CustomSocialAppAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'client_id')
    filter_horizontal = ('sites',)

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
    list_display = ('name', 'type', 'slug')
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
            'name', 'price', 'price_visibility', 'description', 'documentation', 'documentation_label',
            'status', 'stock', 'image', 'slug', 'subcategory', 'category',
            'meta_title', 'meta_description'  # ✅ Added SEO fields to import/export
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

# Product Admin with SEO fields
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    inlines = [SpecificationTableInline]
    list_display = ('name', 'subcategory', 'get_category', 'price', 'price_visibility', 'status', 'stock', 'image_preview', 'documentation_preview', 'has_seo')
    list_filter = ('price_visibility', 'status', 'subcategory__category')
    readonly_fields = ('get_category', 'image_preview', 'slug')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'subcategory')
        }),
        ('Inventory', {
            'fields': ('stock', 'status'),
            'description': 'Stock quantity and availability status. Status is auto-updated based on stock.'
        }),
        ('Pricing', {
            'fields': ('price', 'price_visibility'),
            'description': 'Set the price and choose who can see it.'
        }),
        ('Content', {
            'fields': ('description', 'features', 'image')
        }),
        ('Documentation', {
            'fields': ('documentation', 'documentation_label'),
            'description': 'Enter the URL for the product datasheet and the text to display for the link.'
        }),
        # ✅ NEW SEO Section
        ('SEO (Search Engine Optimization)', {
            'fields': ('meta_title', 'meta_description'),
            'description': 'Optional: Override auto-generated SEO tags. Leave blank to use automatic generation.',
            'classes': ('collapse',)  # Makes it collapsible to keep UI clean
        }),
    )

    def get_category(self, obj):
        return obj.subcategory.category if obj.subcategory else None
    get_category.short_description = 'Category'

    def has_seo(self, obj):
        """Show if product has custom SEO set"""
        if obj.meta_title or obj.meta_description:
            return mark_safe('<span style="color: green;">✓ Custom</span>')
        return mark_safe('<span style="color: gray;">Auto</span>')
    has_seo.short_description = 'SEO'

    def image_preview(self, obj):
        if obj.image:
            try:
                # Use the CloudinaryField's URL method
                if hasattr(obj.image, 'url'):
                    image_url = obj.image.url
                elif hasattr(obj.image, 'build_url'):
                    image_url = obj.image.build_url()
                else:
                    # Fallback for string representations
                    image_str = str(obj.image)
                    if image_str.startswith('http'):
                        image_url = image_str
                    else:
                        image_url = f'https://res.cloudinary.com/ddwpy1x3v/{image_str}'
                
                return mark_safe(f'<img src="{image_url}" style="width: 50px; height: 50px; object-fit: cover;" />')
            except Exception as e:
                return f"Image Error: {str(e)}"
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

    def save_model(self, request, obj, form, change):
        """Override save to ensure slug is generated and status is properly set"""
        # The model's save method will handle slug generation and status updates
        super().save_model(request, obj, form, change)

# Register models
admin.site.register(Category, CategoryAdmin)
admin.site.register(Subcategory, SubcategoryAdmin)
admin.site.register(Product, ProductAdmin)

# Register SpecificationTable and SpecificationRow with basic admin
@admin.register(SpecificationTable)
class SpecificationTableAdmin(admin.ModelAdmin):
    inlines = [SpecificationRowInline]
    list_display = ('title', 'product')
    list_filter = ('product__subcategory__category',)

@admin.register(SpecificationRow)
class SpecificationRowAdmin(admin.ModelAdmin):
    list_display = ('table', 'key', 'value')
    list_filter = ('table__product__subcategory__category',)

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'source_name', 'is_published', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content', 'source_name')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'is_published')
        }),
        ('Content', {
            'fields': ('content', 'image')
        }),
        ('Source Attribution', {
            'fields': ('source_name', 'source_url'),
            'description': 'Credit external sources if applicable'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('slug',)
        return self.readonly_fields