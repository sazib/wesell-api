from rest_framework import serializers

from accounts.serializers import UserSerializer
from catalog.serializers import DeliveryAreaSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product_name", "size", "flavor", "quantity", "unit_price", "discount", "line_total")


class OrderSerializer(serializers.ModelSerializer):
    get_status_display = serializers.CharField(read_only=True)
    get_payment_status_display = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)
    delivery_area = DeliveryAreaSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    get_absolute_url = serializers.SerializerMethodField()
    get_items = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "order_number",
            "status",
            "get_status_display",
            "payment_status",
            "get_payment_status_display",
            "payment_reference",
            "payment_gateway",
            "full_name",
            "phone",
            "email",
            "address",
            "city",
            "notes",
            "grid_coords",
            "delivery_area",
            "delivery_fee",
            "delivery_date",
            "delivery_time_slot",
            "subtotal",
            "discount",
            "total",
            "is_custom_order",
            "custom_cake",
            "user",
            "items",
            "item_count",
            "get_absolute_url",
            "get_items",
            "created",
        )

    def get_get_absolute_url(self, obj):
        return f"/order/{obj.order_number}/"

    def get_get_items(self, obj):
        return {"count": obj.items.count()}

    def get_item_count(self, obj):
        return obj.items.count()


class OrderSummarySerializer(OrderSerializer):
    """Lightweight order payload for dashboards and the orders list."""

    class Meta(OrderSerializer.Meta):
        fields = (
            "id",
            "order_number",
            "status",
            "get_status_display",
            "payment_status",
            "get_payment_status_display",
            "total",
            "delivery_date",
            "is_custom_order",
            "get_absolute_url",
            "get_items",
            "created",
        )


class OrderCreateSerializer(serializers.Serializer):
    cart_key = serializers.CharField(required=False, allow_blank=True)
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    grid_coords = serializers.CharField(required=False, allow_blank=True)
    delivery_area_id = serializers.IntegerField(required=False, allow_null=True)
    delivery_date = serializers.DateField(required=False, allow_null=True)
    delivery_time_slot = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class CustomCakeSerializer(serializers.Serializer):
    occasion = serializers.CharField(max_length=100)
    theme = serializers.CharField(required=False, allow_blank=True)
    size = serializers.ChoiceField(
        choices=["half_kg", "one_kg", "two_kg", "small", "medium", "large"]
    )
    flavor = serializers.ChoiceField(
        choices=[
            "vanilla",
            "chocolate",
            "red_velvet",
            "strawberry",
            "butterscotch",
            "pineapple",
            "mango",
            "eggless_chocolate",
            "eggless_vanilla",
        ]
    )
    filling = serializers.ChoiceField(
        choices=["", "cream", "chocolate_ganache", "fruit", "cheese", "jam"],
        required=False,
        allow_blank=True,
    )
    quantity = serializers.IntegerField(min_value=1, max_value=20, default=1)
    reference_photo = serializers.ImageField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)