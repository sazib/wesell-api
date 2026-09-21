import secrets
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from cart.cart_service import CartService
from orders.serializers import OrderSummarySerializer

from .models import CustomUser, PasswordResetToken
from .serializers import (
    EmailUsernameLoginSerializer,
    ProfileSerializer,
    RegisterSerializer,
    UserSerializer,
)

OTP_EXPIRY_MINUTES = 15


def _token_for(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    cart_key = serializer.validated_data.get("cart_key") or ""
    CartService.get_or_create_for_user(user, cart_key=cart_key)
    return Response(
        {
            "token": _token_for(user).key,
            "user": UserSerializer(user, context={"request": request}).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = EmailUsernameLoginSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data["user"]
    cart_key = serializer.validated_data.get("cart_key") or ""
    CartService.get_or_create_for_user(user, cart_key=cart_key)
    return Response(
        {
            "token": _token_for(user).key,
            "user": UserSerializer(user, context={"request": request}).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    request.user.auth_token.delete()
    return Response({"detail": "Logged out."})


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    if request.method == "PATCH":
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
    serializer = UserSerializer(request.user, context={"request": request})
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    orders = request.user.orders.order_by("-created")[:5]
    data = {
        "user": UserSerializer(request.user, context={"request": request}).data,
        "orders": OrderSummarySerializer(
            orders, many=True, context={"request": request}
        ).data,
    }
    return Response(data)


def _send_otp_email(user, otp):
    subject = "Your Sweet Treats Bakery password reset code"
    message = (
        f"Hi {user.get_full_name() or user.username},\n\n"
        f"Use the following code to reset your password:\n\n{otp}\n\n"
        f"This code expires in {OTP_EXPIRY_MINUTES} minutes. "
        "If you didn't request a password reset, you can safely ignore this email.\n\n"
        "- Sweet Treats Bakery"
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_request(request):
    email = (request.data.get("email") or "").strip()
    if not email:
        return Response({"email": ["Enter an email address."]}, status=status.HTTP_400_BAD_REQUEST)
    user = CustomUser.objects.filter(email__iexact=email).first()
    if not user:
        return Response(
            {"email": ["No account is registered with this email address."]},
            status=status.HTTP_404_NOT_FOUND,
        )
    user.reset_tokens.filter(is_used=False).delete()
    otp = f"{secrets.randbelow(1_000_000):06d}"
    PasswordResetToken.objects.create(
        user=user,
        otp=otp,
        expires_at=timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    )
    _send_otp_email(user, otp)
    return Response(
        {"detail": f"We emailed a verification code to {email}. It expires in {OTP_EXPIRY_MINUTES} minutes."}
    )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_verify(request):
    email = (request.data.get("email") or "").strip()
    otp = request.data.get("otp", "")
    if not email or not otp:
        return Response({"otp": ["Please provide your email and the 6-digit code."]}, status=status.HTTP_400_BAD_REQUEST)
    user = CustomUser.objects.filter(email__iexact=email).first()
    token = (
        PasswordResetToken.objects.filter(user=user, is_used=False).latest("created_at")
        if user
        else None
    )
    if token is None or token.otp != otp or token.is_expired():
        return Response({"otp": ["Invalid or expired code. Please try again."]}, status=status.HTTP_400_BAD_REQUEST)
    token.is_used = True
    token.save()
    return Response({"user_id": user.pk, "email": email})


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request):
    user_id = request.data.get("user_id")
    new_password = request.data.get("new_password1", "")
    password2 = request.data.get("new_password2", "")
    user = CustomUser.objects.filter(pk=user_id).first()
    if not user:
        return Response({"detail": "Your reset session expired. Please request a new code."}, status=status.HTTP_400_BAD_REQUEST)
    if len(new_password) < 8 or new_password != password2:
        return Response(
            {"new_password1": ["Please enter a valid password and confirm it correctly."]},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        user.set_password(new_password)
        user.save()
    except Exception:
        return Response({"new_password1": ["This password is too weak. Try a different one."]}, status=status.HTTP_400_BAD_REQUEST)
    user.reset_tokens.all().delete()
    return Response({"detail": "Password updated! You can now log in with your new password."})