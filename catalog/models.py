from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category-detail", kwargs={"slug": self.slug})


class Product(models.Model):
    class Size(models.TextChoices):
        SMALL = "small", "Small (6\")"
        MEDIUM = "medium", "Medium (8\")"
        LARGE = "large", "Large (10\")"
        EXTRA_LARGE = "xl", "Extra Large (12\")"
        HALF_KG = "half_kg", "Half Kg"
        ONE_KG = "one_kg", "1 Kg"
        TWO_KG = "two_kg", "2 Kg"

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to="products/")
    gallery = models.ManyToManyField("ProductImage", blank=True, related_name="product")
    sizes = models.JSONField(default=list, blank=True, help_text="Available sizes e.g. ['small','medium','large']")
    flavors = models.JSONField(default=list, blank=True, help_text="Available flavors e.g. ['vanilla','chocolate']")
    is_customizable = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)
    advance_order_days = models.PositiveIntegerField(
        default=2, help_text="Minimum days in advance to order this product"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product-detail", kwargs={"slug": self.slug})

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.base_price

    @property
    def is_on_sale(self):
        return self.sale_price is not None and self.sale_price < self.base_price


class ProductImage(models.Model):
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return self.alt_text or f"Image {self.pk}"


class DeliveryArea(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estimated_time = models.CharField(max_length=50, blank=True, help_text="e.g. '30-45 min'")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "delivery areas"
        ordering = ["delivery_fee"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)