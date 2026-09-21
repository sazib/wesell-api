from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ValidationErrorResponse(APIException):
    """Carries structured field errors so the frontend can render them."""


def api_exception_handler(exc, context):
    """Normalise HTTP 4xx/5xx into a consistent {detail|[field]: [errors]} shape."""
    response = exception_handler(exc, context)
    if response is not None:
        if isinstance(response.data, dict):
            return response
        response.data = {"detail": response.data}
        return response

    msg = "Something went wrong. Please try again later."
    return Response({"detail": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)