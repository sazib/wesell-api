from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home_alias"),
    path("nav/", views.nav, name="nav"),
    path("search/", views.search, name="search"),
    path("products/", views.product_list, name="product-list"),
    path("products/<slug:slug>/", views.product_detail, name="product-detail"),
    path("categories/", views.category_list, name="category-list"),
    path("categories/<slug:slug>/", views.category_detail, name="category-detail"),
    path("delivery-areas/", views.delivery_area_list, name="delivery-area-list"),
]