from rest_framework import serializers

from .models import CountdownOffer


class OfferSerializer(serializers.ModelSerializer):
    get_absolute_url = serializers.SerializerMethodField()
    is_running = serializers.BooleanField(read_only=True)
    seconds_left = serializers.IntegerField(read_only=True)
    remaining_seconds = serializers.IntegerField(read_only=True)

    class Meta:
        model = CountdownOffer
        fields = (
            "id",
            "name",
            "slug",
            "discount_percent",
            "banner_message",
            "starts_at",
            "ends_at",
            "is_active",
            "is_running",
            "seconds_left",
            "remaining_seconds",
            "get_absolute_url",
        )

    def get_get_absolute_url(self, obj):
        return f"/offers/{obj.slug}/"