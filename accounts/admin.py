from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, PasswordHistory, PasswordResetToken


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "phone", "city", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Bakery Profile", {"fields": ("phone", "address", "city", "whatsapp_number", "avatar")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Bakery Profile", {"fields": ("phone", "address", "city", "whatsapp_number")}),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "created_at", "expires_at", "is_used")
    list_filter = ("is_used",)
    search_fields = ("user__email", "user__username", "otp")


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__email", "user__username")