from django.urls import path

from . import views

app_name = "offers"

urlpatterns = [
    path("", views.offer_list, name="list"),
    path("<slug:slug>/", views.offer_detail, name="detail"),
]