from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from .models import CustomUser, PasswordHistory


class UserSerializer(serializers.ModelSerializer):
    """Read-only user payload shared across the API."""

    get_full_name = serializers.CharField(read_only=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "city",
            "whatsapp_number",
            "avatar",
            "get_full_name",
        )
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password1 = serializers.CharField(write_only=True, trim_whitespace=False)
    password2 = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    whatsapp_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    cart_key = serializers.CharField(required=False, allow_blank=True)

    def validate_username(self, value):
        if CustomUser.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs.get("password1") != attrs.get("password2"):
            raise serializers.ValidationError({"password2": "The two password fields didn't match."})
        validate_password(attrs.get("password1"))
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = CustomUser(
            username=validated_data["username"],
            email=validated_data["email"].lower(),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            phone=validated_data.get("phone", ""),
            whatsapp_number=validated_data.get("whatsapp_number", ""),
        )
        user.set_password(validated_data["password1"])
        user.save()
        PasswordHistory.objects.create(user=user, password_hash=user.password)
        return user


class EmailUsernameLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)
    cart_key = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError(
                "Please enter a correct email/username and password. Note that both fields may be case-sensitive."
            )
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")
        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = (
            "first_name",
            "last_name",
            "email",
            "phone",
            "whatsapp_number",
            "address",
            "city",
            "avatar",
        )
        extra_kwargs = {
            "email": {"required": False, "allow_blank": True},
        }

    def validate_email(self, value):
        email = (value or "").strip()
        if not email:
            return email
        user = self.instance
        if CustomUser.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email