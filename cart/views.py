from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from catalog.models import Product

from .cart_service import CartService
from .models import CartItem
from .serializers import (
    AddCartItemSerializer,
    CartDetailSerializer,
    UpdateCartItemSerializer,
)


def _cart_context(request):
    user = request.user if request.user.is_authenticated else None
    cart_key = request.query_params.get("cart_key") or ""
    if request.method != "GET":
        data_cart_key = request.data.get("cart_key") if hasattr(request.data, "get") else None
        cart_key = cart_key or data_cart_key or ""
    return user, cart_key


def _serialize(cart, request):
    if cart is None:
        return CartDetailSerializer(data={"items": [], "subtotal": "0.00", "total_items": 0, "is_empty": True}).initial_data
    return CartDetailSerializer(cart, context={"request": request}).data


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def cart_detail(request):
    user, cart_key = _cart_context(request)
    cart = CartService.resolve(user, cart_key)
    return Response(_serialize(cart, request))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def cart_add(request):
    serializer = AddCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    product = Product.objects.filter(slug=data["product_slug"], is_available=True).first()
    if not product:
        return Response({"product_slug": ["No product matches the given slug."]}, status=status.HTTP_404_NOT_FOUND)

    user, cart_key = _cart_context(request)
    cart = CartService.get_or_create_cart(user, cart_key)
    if cart is None:
        return Response(
            {"cart_key": ["A cart key or authenticated user is required."]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    CartService.add_item(
        cart,
        product,
        quantity=data["quantity"],
        size=data.get("size", ""),
        flavor=data.get("flavor", ""),
    )
    return Response(_serialize(cart, request), status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([permissions.AllowAny])
def cart_item(request, item_id):
    item = CartItem.objects.filter(pk=item_id).first()
    if not item:
        return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        cart = item.cart
        CartService.remove_item(item)
        return Response(_serialize(cart, request))

    serializer = UpdateCartItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    cart = item.cart
    CartService.update_item(item, serializer.validated_data["quantity"])
    return Response(_serialize(cart, request))


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def cart_clear(request):
    user, cart_key = _cart_context(request)
    cart = CartService.resolve(user, cart_key)
    if cart:
        CartService.clear(cart)
    return Response(_serialize(CartService.resolve(user, cart_key), request))


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def cart_count(request):
    user, cart_key = _cart_context(request)
    cart = CartService.resolve(user, cart_key)
    return Response({"count": cart.total_items if cart else 0})