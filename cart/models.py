from django.conf import settings
from django.db import models

from catalog.models import DeliveryArea, Product


class Cart(models.Model):
    session_key = models.CharField(max_length=255, blank=True, db_index=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart", null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "carts"

    def __str__(self):
        return f"Cart {self.pk}"

    def get_items(self):
        return self.items.select_related("product")

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def is_empty(self):
        return self.items.count() == 0

    def merge_session_to_user(self, user):
        if not user or self.user == user:
            return
        try:
            user_cart = Cart.objects.get(user=user)
        except Cart.DoesNotExist:
            user_cart = Cart.objects.create(user=user)
        for item in self.items.all():
            existing = user_cart.items.filter(
                product=item.product,
                size=item.size,
                flavor=item.flavor,
            ).first()
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = user_cart
                item.save()
        self.delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=20, blank=True)
    flavor = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "cart items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity