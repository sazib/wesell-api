from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="detail"),
    path("items/", views.cart_add, name="add"),
    path("items/<int:item_id>/", views.cart_item, name="item"),
    path("clear/", views.cart_clear, name="clear"),
    path("count/", views.cart_count, name="count"),
]