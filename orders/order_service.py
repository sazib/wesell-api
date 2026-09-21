"""Order pricing and creation logic (moved from the frontend monolith)."""

import datetime
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from catalog.models import DeliveryArea
from offers.models import CountdownOffer

from .models import Order, OrderItem
from .payments import create_payment

CUSTOM_CAKE_BASE = Decimal("500.00")
CUSTOM_CAKE_SIZE_EXTRA = {
    "half_kg": Decimal("100.00"),
    "one_kg": Decimal("500.00"),
    "two_kg": Decimal("1300.00"),
    "small": Decimal("200.00"),
    "medium": Decimal("450.00"),
    "large": Decimal("800.00"),
}
CUSTOM_CAKE_FLAVOR_EXTRA = {
    "red_velvet": Decimal("300.00"),
    "butterscotch": Decimal("250.00"),
    "mango": Decimal("200.00"),
    "eggless_chocolate": Decimal("150.00"),
    "eggless_vanilla": Decimal("150.00"),
}
CUSTOM_CAKE_FILLING_EXTRA = {
    "chocolate_ganache": Decimal("150.00"),
    "cheese": Decimal("200.00"),
    "fruit": Decimal("100.00"),
}


def money(value):
    return (value or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def running_offer():
    offer = CountdownOffer.objects.filter(is_active=True).order_by("-ends_at").first()
    return offer if offer and offer.is_running else None


def offer_product_ids(offer=None):
    offer = offer or running_offer()
    if not offer:
        return []
    return list(offer.products.filter(is_available=True).values_list("pk", flat=True))


def parse_delivery_date(value):
    if not value:
        return None
    try:
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return value
        return datetime.date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


class OrderService:
    @staticmethod
    def checkout_blueprint(user, cart_key):
        """Everything the checkout/confirmation screens need in one call."""
        from .blueprint import build_checkout_blueprint

        return build_checkout_blueprint(user, cart_key)

    @staticmethod
    def totals_for_cart(cart_items, payload, offer=None):
        """Compute authoritative delivery/discount/subtotal/total for a cart."""
        delivery_area = None
        if payload.get("delivery_area_id"):
            delivery_area = DeliveryArea.objects.filter(pk=payload["delivery_area_id"]).first()
        delivery_fee = delivery_area.delivery_fee if delivery_area else Decimal("0")

        offer = offer if offer is not None else running_offer()
        offer_ids = offer_product_ids(offer)
        discount = Decimal("0")
        subtotal = Decimal("0")
        for item in cart_items:
            subtotal += item.line_total
            if offer and item.product_id in offer_ids:
                unit_discount = item.unit_price * (Decimal(offer.discount_percent) / Decimal("100"))
                discount += unit_discount * item.quantity

        total = subtotal - discount + delivery_fee
        return {
            "delivery_area": delivery_area,
            "delivery_fee": money(delivery_fee),
            "discount": money(discount),
            "subtotal": money(subtotal),
            "total": money(total),
        }

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user, cart, payload, offer=None):
        """Create an Order from a cart + checkout payload. Returns a dict."""
        if cart is None or cart.is_empty:
            return {"success": False, "error": "cart_empty"}

        offer = offer if offer is not None else running_offer()
        offer_ids = offer_product_ids(offer)
        totals = OrderService.totals_for_cart(cart.get_items(), payload, offer)

        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            full_name=payload["full_name"],
            phone=payload["phone"],
            email=payload.get("email", ""),
            address=payload["address"],
            city=payload["city"],
            grid_coords=payload.get("grid_coords", ""),
            delivery_area=totals["delivery_area"],
            delivery_fee=totals["delivery_fee"],
            delivery_date=parse_delivery_date(payload.get("delivery_date")),
            delivery_time_slot=payload.get("delivery_time_slot", ""),
            notes=payload.get("notes", ""),
        )

        discount_total = Decimal("0")
        for item in cart.get_items():
            unit_discount = Decimal("0")
            if offer and item.product_id in offer_ids:
                unit_discount = item.unit_price * (Decimal(offer.discount_percent) / Decimal("100"))
            line_discount = unit_discount * item.quantity
            discount_total += line_discount
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                size=item.size,
                flavor=item.flavor,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=line_discount,
            )
        order.discount = discount_total
        order.recalculate_totals()

        payment = create_payment(order)
        result = {"success": True, "order": order, "payment": payment}

        if payment["success"] and payment["gateway"] == "sandbox":
            order.payment_status = Order.PaymentStatus.PAID
            order.payment_reference = payment["reference"]
            order.payment_gateway = payment["gateway"]
            order.save()
            cart.items.all().delete()
            result["paid"] = True
            result["redirect_url"] = None
            return result

        if payment["success"]:
            order.payment_reference = payment["reference"]
            order.payment_gateway = payment["gateway"]
            order.save()
            result["paid"] = False
            result["redirect_url"] = payment.get("redirect_url")
            return result

        order.status = Order.Status.CANCELLED
        order.payment_status = Order.PaymentStatus.FAILED
        order.save()
        result["success"] = False
        result["paid"] = False
        result["error"] = payment.get("error", "Unknown error")
        return result

    @staticmethod
    @transaction.atomic
    def create_custom_order(user, data, photo_file=None):
        """Create a custom-order request. Returns (order, error)."""
        price = CUSTOM_CAKE_BASE
        price += CUSTOM_CAKE_SIZE_EXTRA.get(data["size"], Decimal("0"))
        price += CUSTOM_CAKE_FLAVOR_EXTRA.get(data["flavor"], Decimal("0"))
        price += CUSTOM_CAKE_FILLING_EXTRA.get(data.get("filling", ""), Decimal("0"))

        photo_name = ""
        if photo_file:
            photo_name = photo_file.name

        order = Order.objects.create(
            user=user if user and user.is_authenticated else None,
            full_name=user.get_full_name() if user and user.is_authenticated else "Custom Cake Customer",
            phone=user.phone if user and user.is_authenticated else "",
            email=user.email if user and user.is_authenticated else "",
            address=user.address if user and user.is_authenticated else "",
            city=user.city if user and user.is_authenticated else "",
            notes=data.get("notes", ""),
            delivery_date=None,
            subtotal=price * data["quantity"],
            total=price * data["quantity"],
            is_custom_order=True,
            custom_cake={
                "occasion": data["occasion"],
                "theme": data.get("theme", ""),
                "size": data["size"],
                "flavor": data["flavor"],
                "filling": data.get("filling", ""),
                "quantity": data["quantity"],
                "reference_photo": photo_name,
            },
            payment_status=Order.PaymentStatus.UNPAID,
        )
        return order, None