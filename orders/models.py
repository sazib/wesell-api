from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse

from catalog.models import DeliveryArea, Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PREPARING = "preparing", "In Preparation"
        OUT_FOR_DELIVERY = "out_for_delivery", "Out For Delivery"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "Unpaid"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100)
    notes = models.TextField(blank=True)
    grid_coords = models.CharField(max_length=100, blank=True, help_text="Optional map coordinates")

    delivery_area = models.ForeignKey(DeliveryArea, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal("0"))
    delivery_date = models.DateField(null=True, blank=True, help_text="Requested delivery date (advance order)")
    delivery_time_slot = models.CharField(max_length=100, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_reference = models.CharField(max_length=200, blank=True)
    payment_gateway = models.CharField(max_length=50, blank=True)

    is_custom_order = models.BooleanField(default=False, help_text="True for custom-designed cakes")
    custom_cake = models.JSONField(default=dict, blank=True, help_text="Custom design details")

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_order_number():
        return "BK-{seq:06d}".format(seq=Order.objects.count() + 1)

    def get_absolute_url(self):
        return reverse("orders:detail", kwargs={"order_number": self.order_number})

    def get_items(self):
        return self.items.select_related("product")

    def recalculate_totals(self):
        self.subtotal = sum(item.line_total for item in self.items.all())
        self.discount = sum(item.discount for item in self.items.all())
        self.total = self.subtotal - self.discount + self.delivery_fee
        self.save()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="order_items")
    product_name = models.CharField(max_length=200)
    size = models.CharField(max_length=20, blank=True)
    flavor = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    class Meta:
        verbose_name_plural = "order items"

    def __str__(self):
        return self.product_name

    @property
    def line_total(self):
        return self.unit_price * self.quantity