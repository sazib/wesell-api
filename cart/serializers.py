from decimal import Decimal

from rest_framework import serializers

from catalog.serializers import ProductSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "size", "flavor", "unit_price", "line_total")


class CartDetailSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "subtotal", "total_items", "is_empty", "updated")


class AddCartItemSerializer(serializers.Serializer):
    product_slug = serializers.SlugField()
    quantity = serializers.IntegerField(min_value=1, max_value=99, default=1)
    size = serializers.CharField(required=False, allow_blank=True, default="")
    flavor = serializers.CharField(required=False, allow_blank=True, default="")
    cart_key = serializers.CharField(required=False, allow_blank=True)


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1, max_value=99)