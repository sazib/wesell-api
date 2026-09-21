from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "quantity", "unit_price", "discount")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "full_name",
        "phone",
        "total",
        "status",
        "payment_status",
        "delivery_date",
        "created",
    )
    list_filter = ("status", "payment_status", "delivery_date", "is_custom_order")
    list_editable = ("status", "payment_status")
    search_fields = ("order_number", "full_name", "phone", "email")
    inlines = [OrderItemInline]
    readonly_fields = ("order_number", "created", "updated")
    fieldsets = (
        ("Order", {"fields": ("order_number", "user", "status", "payment_status", "payment_reference", "is_custom_order")}),
        ("Customer", {"fields": ("full_name", "phone", "email", "address", "city", "grid_coords", "notes")}),
        ("Delivery", {"fields": ("delivery_area", "delivery_fee", "delivery_date", "delivery_time_slot")}),
        ("Totals", {"fields": ("subtotal", "discount", "total")}),
        ("Custom Cake", {"fields": ("custom_cake",)}),
        ("Timestamps", {"fields": ("created", "updated")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product_name", "quantity", "size", "flavor", "unit_price", "line_total")
    search_fields = ("order__order_number", "product_name")