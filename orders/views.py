from django.core.mail import send_mail
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from cart.cart_service import CartService

from .blueprint import build_checkout_blueprint
from .models import Order
from .order_service import OrderService, CUSTOM_CAKE_BASE, CUSTOM_CAKE_SIZE_EXTRA
from .payments import verify_payment
from .serializers import (
    CustomCakeSerializer,
    OrderCreateSerializer,
    OrderSerializer,
    OrderSummarySerializer,
)


def _current_user(request):
    return request.user if request.user.is_authenticated else None


def _cart_key_for(request):
    return request.query_params.get("cart_key") or request.data.get("cart_key") or ""


def _send_confirmation(order):
    try:
        if order.email:
            send_mail(
                subject=f"Order {order.order_number} confirmed",
                message=(
                    f"Hi {order.full_name},\n\n"
                    f"Your order {order.order_number} has been received.\n"
                    f"Total: {order.total}\n"
                    f"Expected delivery: {order.delivery_date}\n\n"
                    f"Thank you for ordering with us!"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
    except TypeError:
        pass


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def checkout_blueprint(request):
    return Response(build_checkout_blueprint(_current_user(request), _cart_key_for(request)))


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def custom_cake_meta(request):
    return Response(
        {
            "base_price": str(CUSTOM_CAKE_BASE),
            "size_extras": {k: str(v) for k, v in CUSTOM_CAKE_SIZE_EXTRA.items()},
        }
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def create_order(request):
    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    user = _current_user(request)
    cart_key = payload.get("cart_key") or _cart_key_for(request)
    cart = CartService.resolve(user, cart_key)
    if cart is None or cart.is_empty:
        return Response(
            {"detail": "Your cart is empty. Add some treats first."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = OrderService.create_order_from_cart(user, cart, payload)
    if not result["success"]:
        return Response(
            {"detail": "Payment failed: " + result.get("error", "Unknown error")},
            status=status.HTTP_402_PAYMENT_REQUIRED,
        )

    order = result["order"]
    body = {
        "order": OrderSerializer(order, context={"request": request}).data,
        "paid": result.get("paid", False),
        "redirect_url": result.get("redirect_url"),
    }
    status_code = status.HTTP_201_CREATED
    if not result.get("paid"):
        status_code = status.HTTP_202_ACCEPTED
    return Response(body, status=status_code)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def create_custom_order(request):
    serializer = CustomCakeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    photo = data.get("reference_photo")
    order, error = OrderService.create_custom_order(_current_user(request), data, photo_file=photo)
    if error:
        return Response({"detail": error}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "order": OrderSerializer(order, context={"request": request}).data,
            "detail": "Your custom cake request was received! We will contact you shortly to confirm details and payment.",
        },
        status=status.HTTP_201_CREATED,
    )


def _order_or_none(order_number):
    return Order.objects.select_related("user", "delivery_area").filter(order_number=order_number).first()


def _can_view(request, order):
    if order.user is None:
        return True
    return request.user.is_authenticated and order.user_id == request.user.id


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def order_detail(request, order_number):
    order = _order_or_none(order_number)
    if not order:
        return Response({"detail": "No Order matches the given query."}, status=status.HTTP_404_NOT_FOUND)
    if not _can_view(request, order):
        return Response(
            {"detail": "You are not allowed to view that order."},
            status=status.HTTP_403_FORBIDDEN,
        )
    return Response(OrderSerializer(order, context={"request": request}).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def order_list(request):
    orders = request.user.orders.order_by("-created").select_related("delivery_area")
    active = orders.exclude(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
    past = orders.filter(status__in=[Order.Status.DELIVERED, Order.Status.CANCELLED])
    ctx = {"request": request}
    return Response(
        {
            "active": OrderSummarySerializer(active, many=True, context=ctx).data,
            "past": OrderSummarySerializer(past, many=True, context=ctx).data,
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def cancel_order(request, order_number):
    order = request.user.orders.filter(order_number=order_number).first()
    if not order:
        return Response({"detail": "No Order matches the given query."}, status=status.HTTP_404_NOT_FOUND)
    if order.status == Order.Status.PENDING:
        order.status = Order.Status.CANCELLED
        order.save()
        return Response({"detail": "Order cancelled."})
    return Response(
        {"detail": "This order cannot be cancelled at this stage."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def confirm_payment(request, order_number):
    order = _order_or_none(order_number)
    if not order:
        return Response({"detail": "No Order matches the given query."}, status=status.HTTP_404_NOT_FOUND)
    if not _can_view(request, order):
        return Response({"detail": "You are not allowed to view that order."}, status=status.HTTP_403_FORBIDDEN)
    verified = verify_payment(order)
    if verified and order.payment_status != Order.PaymentStatus.PAID:
        order.payment_status = Order.PaymentStatus.PAID
        order.save()
        _send_confirmation(order)
        return Response({"detail": "Payment confirmed."})
    return Response({"detail": "Could not verify payment."}, status=status.HTTP_400_BAD_REQUEST)