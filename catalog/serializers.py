from django.db.models import Avg, Count
from rest_framework import serializers

from offers.models import CountdownOffer
from reviews.models import Review

from .models import Category, DeliveryArea, Product, ProductImage


def absolute_file_url(request, file_field):
    """Build an absolute URL for an uploaded file.

    Prefers PUBLIC_BASE_URL (set in production behind a proxy), otherwise
    falls back to the incoming request host.
    """
    from django.conf import settings

    if file_field is None or not file_field:
        return None
    path = file_field.url
    base = settings.PUBLIC_BASE_URL
    if not base and request is not None:
        base = request.build_absolute_uri("/").rstrip("/")
    if base:
        return f"{base}{path}"
    return path


class ProductImageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ("id", "url", "alt_text")

    def get_url(self, obj):
        return absolute_file_url(self.context.get("request"), obj.image)


class CategorySummarySerializer(serializers.ModelSerializer):
    """Category embedded inside product payloads."""

    get_absolute_url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "get_absolute_url")

    def get_get_absolute_url(self, obj):
        return f"/category/{obj.slug}/"


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    get_absolute_url = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "sort_order",
            "get_absolute_url",
            "products",
        )

    def get_image(self, obj):
        if not obj.image:
            return None
        return {"url": absolute_file_url(self.context.get("request"), obj.image)}

    def get_get_absolute_url(self, obj):
        return f"/category/{obj.slug}/"

    def get_products(self, obj):
        return {"count": obj.products.filter(is_available=True).count()}


def _running_offer():
    offer = CountdownOffer.objects.filter(is_active=True).order_by("-ends_at").first()
    return offer if offer and offer.is_running else None


class ProductSerializer(serializers.ModelSerializer):
    current_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    image = serializers.SerializerMethodField()
    gallery = ProductImageSerializer(many=True, read_only=True)
    category = CategorySummarySerializer(read_only=True)
    reviews = serializers.SerializerMethodField()
    get_absolute_url = serializers.SerializerMethodField()
    offer_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "base_price",
            "sale_price",
            "current_price",
            "is_on_sale",
            "offer_price",
            "is_customizable",
            "is_available",
            "stock",
            "advance_order_days",
            "sizes",
            "flavors",
            "image",
            "gallery",
            "category",
            "reviews",
            "get_absolute_url",
        )

    def get_image(self, obj):
        return {"url": absolute_file_url(self.context.get("request"), obj.image)}

    def get_reviews(self, obj):
        count = getattr(obj, "review_count", None)
        avg = getattr(obj, "avg_rating", None)
        if count is None:
            agg = obj.reviews.filter(is_published=True).aggregate(
                avg=Avg("rating"), count=Count("id")
            )
            count, avg = agg["count"] or 0, agg["avg"]
        return {"count": count or 0, "avg": avg}

    def get_get_absolute_url(self, obj):
        return f"/product/{obj.slug}/"

    def get_offer_price(self, obj):
        offer = _running_offer()
        if not offer or not offer.products.filter(pk=obj.pk).exists():
            return None
        from decimal import ROUND_HALF_UP, Decimal

        if obj.sale_price:
            return str(obj.sale_price)
        price = (obj.base_price * offer.discount_multiplier).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return str(price)


class DeliveryAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryArea
        fields = ("id", "name", "slug", "delivery_fee", "estimated_time", "is_active")