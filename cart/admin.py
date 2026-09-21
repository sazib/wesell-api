from django.contrib import admin

from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "total_items", "subtotal", "updated")
    search_fields = ("user__username", "session_key")
    inlines = [CartItemInline]
    readonly_fields = ("created", "updated")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "cart", "product", "quantity", "size", "flavor", "unit_price", "line_total")
    list_filter = ("product",)
    search_fields = ("product__name",)