from django.db import models
from django.utils.text import slugify
import cloudinary
import cloudinary.uploader
from cloudinary.models import CloudinaryField

class Category(models.Model):
    FIRE_SAFETY = 'fire_safety'
    ICT = 'ict'
    SOLAR = 'solar'
    CATEGORY_TYPES = [
        (FIRE_SAFETY, 'Fire Safety'),
        (ICT, 'ICT'),
        (SOLAR, 'Solar')
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=[('fire_safety', 'Fire Safety'), ('ict', 'ICT'), ('solar', 'Solar')], default='fire_safety')
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

class Subcategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Subcategory.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class Product(models.Model):
    # Price visibility choices
    PUBLIC = 'public'
    LOGIN_REQUIRED = 'login_required'
    PRICE_VISIBILITY_CHOICES = [
        (PUBLIC, 'Public'),
        (LOGIN_REQUIRED, 'Login Required'),
    ]

    # Stock status choices - simplified to only two values
    IN_STOCK = 'in_stock'
    OUT_OF_STOCK = 'out_of_stock'
    STOCK_STATUS_CHOICES = [
        (IN_STOCK, 'In Stock'),
        (OUT_OF_STOCK, 'Out of Stock'),
    ]

    subcategory = models.ForeignKey(Subcategory, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_visibility = models.CharField(
        max_length=20, 
        choices=PRICE_VISIBILITY_CHOICES, 
        default=PUBLIC,
        help_text="Choose who can see the price of this product"
    )
    description = models.TextField(blank=True)
    features = models.TextField(blank=True)
    
    # Use CloudinaryField for proper Cloudinary integration
    image = CloudinaryField('image', null=True, blank=True, folder='products')
    
    slug = models.SlugField(unique=True, blank=True)
    documentation = models.URLField(blank=True, null=True, help_text="Enter the URL for the product datasheet")
    documentation_label = models.CharField(max_length=255, blank=True, help_text="Display text for the documentation link (e.g., 'View Datasheet', 'Technical Specs')")
    
    # Updated status field with proper choices and default
    status = models.CharField(
        max_length=20, 
        choices=STOCK_STATUS_CHOICES, 
        default=IN_STOCK,
        help_text="Stock availability status"
    )
    stock = models.PositiveIntegerField(default=0, help_text="Number of items in stock")

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Auto-set stock status based on stock quantity
        if self.stock > 0:
            self.status = self.IN_STOCK
        else:
            self.status = self.OUT_OF_STOCK
            
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        """Helper property to check if product is in stock"""
        return self.status == self.IN_STOCK and self.stock > 0

class SpecificationTable(models.Model):
    """
    Each product can have multiple specification tables.
    Each table can have multiple rows.
    """
    product = models.ForeignKey(Product, related_name='spec_tables', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.title or 'Untitled Table'} - {self.product.name}"

class SpecificationRow(models.Model):
    """
    Each row belongs to one SpecificationTable.
    Rows are stored as key/value pairs.
    Example:
    key="Model", value="Eaton Addressable fire detector"
    """
    table = models.ForeignKey(SpecificationTable, related_name='rows', on_delete=models.CASCADE)
    key = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
    
class Blog(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField()
    content = models.TextField()
    image = models.ImageField(upload_to='blogs/', blank=True, null=True, default='blogs/default.jpeg')
    source_name = models.CharField(max_length=100, blank=True, null=True)
    source_url = models.URLField(blank=True, null=True)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Blog.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title