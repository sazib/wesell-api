from django.contrib import admin

from .models import CountdownOffer


@admin.register(CountdownOffer)
class CountdownOfferAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_percent", "starts_at", "ends_at", "is_active", "is_running")
    list_filter = ("is_active",)
    list_editable = ("is_active",)
    search_fields = ("name", "banner_message")
    filter_horizontal = ("products",)
    prepopulated_fields = {"slug": ("name",)}