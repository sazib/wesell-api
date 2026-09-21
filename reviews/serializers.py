from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "product",
            "rating",
            "title",
            "comment",
            "is_published",
            "created",
            "user",
        )

    def get_user(self, obj):
        return {
            "id": obj.user_id,
            "username": obj.user.username,
            "get_full_name": obj.user.get_full_name(),
        }


class ReviewCreateSerializer(serializers.Serializer):
    product_slug = serializers.SlugField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    title = serializers.CharField(required=False, allow_blank=True, max_length=200)
    comment = serializers.CharField()