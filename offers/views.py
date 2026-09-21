from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from catalog.serializers import ProductSerializer
from catalog.views import _product_queryset

from .models import CountdownOffer
from .serializers import OfferSerializer


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def offer_list(request):
    offers = CountdownOffer.objects.filter(is_active=True)
    now = timezone.now()
    running = [o for o in offers if o.is_running]
    upcoming = [o for o in offers if not o.is_running and o.starts_at > now]
    ctx = {"request": request}
    return Response(
        {
            "running_offers": OfferSerializer(running, many=True, context=ctx).data,
            "upcoming_offers": OfferSerializer(upcoming, many=True, context=ctx).data,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def offer_detail(request, slug):
    offer = CountdownOffer.objects.filter(slug=slug, is_active=True).first()
    if not offer:
        return Response({"detail": "No CountdownOffer matches the given query."}, status=status.HTTP_404_NOT_FOUND)
    products = _product_queryset().filter(offers=offer)
    ctx = {"request": request}
    return Response(
        {
            "offer": OfferSerializer(offer, context=ctx).data,
            "products": ProductSerializer(products, many=True, context=ctx).data,
        }
    )