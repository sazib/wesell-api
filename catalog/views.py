from django.conf import settings
from django.db.models import Avg, Count, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from offers.models import CountdownOffer
from reviews.serializers import ReviewSerializer

from .models import Category, DeliveryArea, Product
from .serializers import (
    CategorySerializer,
    DeliveryAreaSerializer,
    ProductSerializer,
)


def _running_offer():
    offer = CountdownOffer.objects.filter(is_active=True).order_by("-ends_at").first()
    return offer if offer and offer.is_running else None


def _product_queryset():
    return (
        Product.objects.filter(is_available=True)
        .select_related("category")
        .prefetch_related("gallery")
        .annotate(
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_published=True)),
            review_count=Count("reviews__id", filter=Q(reviews__is_published=True)),
        )
    )


def _offer_payload(offer):
    if offer is None:
        return None
    return {
        "id": offer.id,
        "name": offer.name,
        "slug": offer.slug,
        "banner_message": offer.banner_message,
        "discount_percent": offer.discount_percent,
        "starts_at": offer.starts_at.isoformat(),
        "ends_at": offer.ends_at.isoformat(),
        "is_running": offer.is_running,
        "get_absolute_url": f"/offers/{offer.slug}/",
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    featured = _product_queryset().filter(is_featured=True)[:8]
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    newest = _product_queryset().order_by("-created")[:8]
    running_offer = _running_offer()
    offer_products = _product_queryset().filter(offers=running_offer)[:8] if running_offer else []
    ctx = {"request": request}
    return Response(
        {
            "featured": ProductSerializer(featured, many=True, context=ctx).data,
            "categories": CategorySerializer(categories, many=True, context=ctx).data,
            "newest": ProductSerializer(newest, many=True, context=ctx).data,
            "running_offer": _offer_payload(running_offer),
            "offer_products": ProductSerializer(offer_products, many=True, context=ctx).data,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def product_list(request):
    qs = _product_queryset()
    search = request.query_params.get("q", "").strip()
    category = request.query_params.get("category", "").strip()
    featured = request.query_params.get("featured")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if category:
        qs = qs.filter(category__slug=category)
    if featured and featured.lower() in ("1", "true"):
        qs = qs.filter(is_featured=True)
    sort = request.query_params.get("sort", "newest")
    if sort == "price_asc":
        qs = qs.order_by("base_price")
    elif sort == "price_desc":
        qs = qs.order_by("-base_price")
    elif sort == "rating":
        qs = qs.order_by("-avg_rating")
    else:
        qs = qs.order_by("-created")
    return Response(ProductSerializer(qs, many=True, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def product_detail(request, slug):
    product = get_object_or_404_available(slug)
    related = (
        _product_queryset()
        .filter(category=product.category)
        .exclude(pk=product.pk)[:4]
    )
    reviews = product.reviews.filter(is_published=True).select_related("user").order_by("-created")
    ctx = {"request": request}
    return Response(
        {
            "product": ProductSerializer(product, context=ctx).data,
            "reviews": ReviewSerializer(reviews, many=True, context=ctx).data,
            "related": ProductSerializer(related, many=True, context=ctx).data,
        }
    )


def get_object_or_404_available(slug):
    from django.shortcuts import get_object_or_404

    return get_object_or_404(Product, slug=slug, is_available=True)


@api_view(["GET"])
@permission_classes([AllowAny])
def category_list(request):
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    return Response(
        CategorySerializer(categories, many=True, context={"request": request}).data
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def category_detail(request, slug):
    category = Category.objects.filter(slug=slug, is_active=True).first()
    if not category:
        return Response({"detail": "No Category matches the given query."}, status=status.HTTP_404_NOT_FOUND)
    products = _product_queryset().filter(category=category)
    sort = request.query_params.get("sort", "newest")
    if sort == "price_asc":
        products = products.order_by("base_price")
    elif sort == "price_desc":
        products = products.order_by("-base_price")
    elif sort == "rating":
        products = products.order_by("-avg_rating")
    else:
        products = products.order_by("-created")
    ctx = {"request": request}
    return Response(
        {
            "category": CategorySerializer(category, context=ctx).data,
            "products": ProductSerializer(products, many=True, context=ctx).data,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def search(request):
    query = request.query_params.get("q", "").strip()
    products = []
    if query:
        products = _product_queryset().filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    return Response(
        {
            "query": query,
            "products": ProductSerializer(products, many=True, context={"request": request}).data,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def delivery_area_list(request):
    areas = DeliveryArea.objects.filter(is_active=True)
    return Response(DeliveryAreaSerializer(areas, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def nav(request):
    """Single aggregated endpoint powering the frontend chrome on every page."""
    categories = Category.objects.filter(is_active=True).order_by("sort_order", "name")
    running_offer = _running_offer()
    ctx = {"request": request}

    request_has_auth = getattr(request, "user", None) and request.user.is_authenticated

    from cart.cart_service import CartService

    cart_key = request.query_params.get("cart_key", "")
    order = CartService.resolve(request.user if request_has_auth else None, cart_key=cart_key)
    cart_count = order.total_items if order else 0

    return Response(
        {
            "nav_categories": CategorySerializer(categories, many=True, context=ctx).data,
            "running_offer": _offer_payload(running_offer),
            "whatsapp_number": settings.WHATSAPP_NUMBER,
            "messenger_url": settings.MESSENGER_PAGE_URL,
            "authenticated": bool(request_has_auth),
            "cart_count": cart_count,
        }
    )