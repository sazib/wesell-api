from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from catalog.models import Product


class CountdownOffer(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    discount_percent = models.PositiveIntegerField(
        default=10, help_text="Discount percentage applied to opted-in products"
    )
    banner_message = models.CharField(max_length=250, blank=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    products = models.ManyToManyField(Product, blank=True, related_name="offers")
    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-starts_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_running(self):
        now = timezone.now()
        return self.is_active and self.starts_at <= now <= self.ends_at

    @property
    def seconds_left(self):
        return max((self.ends_at - timezone.now()).total_seconds(), 0)

    def get_absolute_url(self):
        return reverse("offers:detail", kwargs={"slug": self.slug})

    @property
    def remaining_seconds(self):
        return max(int(self.seconds_left), 0)

    @property
    def discount_multiplier(self):
        return Decimal(str((100 - self.discount_percent) / 100))