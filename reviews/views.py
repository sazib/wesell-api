from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from catalog.models import Product

from .models import Review
from .serializers import ReviewCreateSerializer, ReviewSerializer


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def add_review(request):
    serializer = ReviewCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    product = Product.objects.filter(slug=data["product_slug"], is_available=True).first()
    if not product:
        return Response({"product_slug": ["No product matches the given slug."]}, status=status.HTTP_404_NOT_FOUND)
    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            "rating": data["rating"],
            "title": data.get("title", ""),
            "comment": data["comment"],
        },
    )
    return Response(
        {
            "review": ReviewSerializer(review, context={"request": request}).data,
            "detail": "Thank you! Your review was published.",
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )