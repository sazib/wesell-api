from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)

    def set_password(self, raw_password):
        if self.pk and self.password:
            PasswordHistory.objects.create(user=self, password_hash=self.password)
        super().set_password(raw_password)
        if self.pk:
            recent_ids = list(
                PasswordHistory.objects.filter(user=self)
                .order_by("-created_at", "-id")
                .values_list("pk", flat=True)[:24]
            )
            PasswordHistory.objects.filter(user=self).exclude(pk__in=recent_ids).delete()

    def __str__(self):
        return self.get_full_name() or self.username

    class Meta:
        ordering = ["-date_joined"]


class PasswordHistory(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="password_history")
    password_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.user.email} - {self.created_at:%Y-%m-%d %H:%M}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="reset_tokens")
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.user.email} - {self.otp}"