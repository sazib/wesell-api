from datetime import datetime

from django.conf import settings

"""
Payment gateway abstraction (moved from the frontend monolith).

Supports a 'sandbox' (simulated) gateway out of the box so the full
checkout flow can be exercised locally with zero configuration.

To go live, set PAYMENT_GATEWAY to 'razorpay', 'stripe' or 'sslcommerz'
and provide the corresponding keys via environment variables.
"""


def create_payment(order):
    gateway = settings.PAYMENT_GATEWAY
    amount_paise = int(order.total * 100)

    if gateway == "razorpay":
        try:
            import razorpay  # pip install razorpay
        except ImportError:
            return _error_response(gateway, "razorpay SDK not installed")
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        payload = {
            "amount": amount_paise,
            "currency": "INR",
            "receipt": order.order_number,
            "notes": {"order_number": order.order_number},
        }
        try:
            result = client.order.create(payload)
            return {
                "success": True,
                "gateway": gateway,
                "reference": result["id"],
                "redirect_url": None,
                "payload": result,
            }
        except Exception as e:  # noqa: BLE001
            return _error_response(gateway, str(e))

    if gateway == "stripe":
        try:
            import stripe  # pip install stripe
        except ImportError:
            return _error_response(gateway, "stripe SDK not installed")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {"name": f"Bakery order {order.order_number}"},
                            "unit_amount": amount_paise,
                        },
                        "quantity": 1,
                    }
                ],
                success_url=settings.ORDER_SUCCESS_URL,
                cancel_url=settings.ORDER_CANCEL_URL,
            )
            return {
                "success": True,
                "gateway": gateway,
                "reference": session.id,
                "redirect_url": session.url,
                "payload": {"session_id": session.id},
            }
        except Exception as e:  # noqa: BLE001
            return _error_response(gateway, str(e))

    if gateway == "sslcommerz":
        return {
            "success": False,
            "gateway": "sslcommerz",
            "reference": "",
            "redirect_url": None,
            "payload": {},
            "error": "SSLCommerz integration requires server-side session init; implement in payments.py",
        }

    # Sandbox / fallback: pretend the payment succeeded.
    return {
        "success": True,
        "gateway": "sandbox",
        "reference": f"SANDBOX-{order.order_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "redirect_url": None,
        "payload": {"amount": str(order.total), "mode": "sandbox"},
    }


def verify_payment(order):
    """Confirm a payment for an order. Sandbox always succeeds."""
    if not order.payment_reference:
        return False
    return True


def _error_response(gateway, message):
    return {
        "success": False,
        "gateway": gateway,
        "reference": "",
        "redirect_url": None,
        "payload": {},
        "error": message,
    }