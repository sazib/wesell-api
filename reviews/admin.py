from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "is_published", "created")
    list_filter = ("is_published", "rating", "product")
    list_editable = ("is_published", "rating")
    search_fields = ("product__name", "user__username", "comment")