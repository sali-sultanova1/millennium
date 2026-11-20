from django.urls import path

from .views import (
    favorites_items_view,
    favorites_view,
    tour_detail_view,
    tour_list_view,
)

app_name = "catalog"

urlpatterns = [
    path("", tour_list_view, name="tour_list"),
    path("favorites/", favorites_view, name="favorites"),
    path("favorites_items/", favorites_items_view, name="favorites_items"),

    path("<slug:slug>/", tour_detail_view, name="tour_detail"),
]