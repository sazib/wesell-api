"""Aggregated payload powering the frontend checkout / confirmation pages."""

from cart.cart_service import CartService
from cart.serializers import CartDetailSerializer
from catalog.models import DeliveryArea
from catalog.serializers import DeliveryAreaSerializer

from .order_service import OrderService, running_offer


def build_checkout_blueprint(user, cart_key):
    cart = CartService.resolve(user, cart_key)
    offer = running_offer()

    cart_items = cart.get_items() if cart else []
    totals = OrderService.totals_for_cart(cart_items, {}, offer)
    totals["discount"] = totals["discount"] if offer else "0.00"

    areas = DeliveryArea.objects.filter(is_active=True)
    return {
        "cart": CartDetailSerializer(cart, context={}).data if cart else {
            "items": [], "subtotal": "0.00", "total_items": 0, "is_empty": True
        },
        "cart_key": cart_key,
        "delivery_areas": DeliveryAreaSerializer(areas, many=True).data,
        "running_offer_id": offer.id if offer else None,
        "offer_data": {
            "id": offer.id,
            "name": offer.name,
            "banner_message": offer.banner_message,
            "discount_percent": offer.discount_percent,
            "ends_at": offer.ends_at.isoformat(),
            "get_absolute_url": f"/offers/{offer.slug}/",
        }
        if offer
        else None,
        "offer_product_ids": list(
            offer.products.filter(is_available=True).values_list("pk", flat=True)
        )
        if offer
        else [],
        "subtotal": totals["subtotal"],
        "discount": totals["discount"],
        "delivery_fee": totals["delivery_fee"],
        "total": totals["total"],
    }