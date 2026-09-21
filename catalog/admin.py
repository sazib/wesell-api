from django.contrib import admin

from .models import Category, DeliveryArea, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = Product.gallery.through
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "base_price",
        "sale_price",
        "is_featured",
        "is_customizable",
        "is_available",
        "stock",
    )
    list_filter = ("category", "is_featured", "is_customizable", "is_available")
    list_editable = ("sale_price", "is_featured", "is_customizable", "is_available", "stock")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created", "updated")
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "description", "image")}),
        ("Pricing", {"fields": ("base_price", "sale_price")}),
        ("Options", {"fields": ("sizes", "flavors", "is_customizable")}),
        ("Stock & Availability", {"fields": ("stock", "is_available", "advance_order_days", "is_featured")}),
        ("Timestamps", {"fields": ("created", "updated")}),
    )


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("alt_text",)
    search_fields = ("alt_text",)


@admin.register(DeliveryArea)
class DeliveryAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "delivery_fee", "estimated_time", "is_active")
    list_editable = ("delivery_fee", "is_active")
    prepopulated_fields = {"slug": ("name",)}