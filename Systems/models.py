from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    FIRE_SAFETY = 'fire_safety'
    ICT = 'ict'
    CATEGORY_TYPES = [
        (FIRE_SAFETY, 'Fire Safety'),
        (ICT, 'ICT'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=[('fire_safety', 'Fire Safety'), ('ict', 'ICT')], default='fire_safety')
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
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True)
    documentation = models.URLField(blank=True, null=True, help_text="Enter the URL for the product datasheet")
    documentation_label = models.CharField(max_length=255, blank=True, help_text="Display text for the documentation link (e.g., 'View Datasheet', 'Technical Specs')")
    status = models.CharField(max_length=50, default='active')
    stock = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

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