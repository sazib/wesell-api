from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("checkout/", views.checkout_blueprint, name="checkout"),
    path("custom-cake/meta/", views.custom_cake_meta, name="custom-cake-meta"),
    path("custom-cake/", views.create_custom_order, name="custom-cake"),
    path("create/", views.create_order, name="create"),
    path("", views.order_list, name="list"),
    path("<str:order_number>/cancel/", views.cancel_order, name="cancel"),
    path("<str:order_number>/payment/confirm/", views.confirm_payment, name="confirm-payment"),
    path("<str:order_number>/", views.order_detail, name="detail"),
]