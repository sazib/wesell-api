"""Cart resolution helpers shared by the cart, auth and order endpoints.

Mirrors the behaviour of the original monolith: a cart is keyed by a
session `cart_key` for guests and by the authenticated user for members.
On login/registration any guest cart is merged into the user's cart.
"""

from .models import Cart, CartItem


class CartService:
    @staticmethod
    def resolve(user=None, cart_key=None):
        """Return the current cart for user/cart_key, or None."""
        if user is not None and user.is_authenticated:
            return Cart.objects.filter(user=user).first()
        if cart_key:
            return Cart.objects.filter(session_key=cart_key).first()
        return None

    @staticmethod
    def get_or_create_cart(user=None, cart_key=None):
        """Return an existing cart or create one for the user/cart_key."""
        if user is not None and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            if cart_key:
                old_cart = (
                    Cart.objects.filter(session_key=cart_key)
                    .exclude(pk=cart.pk)
                    .first()
                )
                if old_cart:
                    old_cart.merge_session_to_user(user)
            return cart
        if not cart_key:
            return None
        cart, _ = Cart.objects.get_or_create(session_key=cart_key)
        return cart

    @staticmethod
    def get_or_create_for_user(user, cart_key=None):
        """Ensure the user owns a cart; merge any guest cart into it."""
        if not user:
            return None
        cart, _ = Cart.objects.get_or_create(user=user)
        if cart_key:
            old_cart = (
                Cart.objects.filter(session_key=cart_key).exclude(pk=cart.pk).first()
            )
            if old_cart:
                old_cart.merge_session_to_user(user)
        return cart

    @staticmethod
    def add_item(cart, product, quantity, size="", flavor=""):
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            size=size,
            flavor=flavor,
            defaults={"quantity": quantity, "unit_price": product.current_price},
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item, created

    @staticmethod
    def update_item(item, quantity):
        item.quantity = quantity
        item.save()
        return item

    @staticmethod
    def remove_item(item):
        item.delete()

    @staticmethod
    def clear(cart):
        cart.items.all().delete()