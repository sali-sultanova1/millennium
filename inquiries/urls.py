from django.urls import path

from .views import (
    favorites_inquiry_create_view,
    inquiry_create_view,
    inquiry_success_view,
    tour_inquiry_create_view,
)

app_name = "inquiries"

urlpatterns = [
    path("", inquiry_create_view, name="create"),
    path("success/", inquiry_success_view, name="success"),
    path("favorites/", favorites_inquiry_create_view, name="favorites_create"),
    path("tour/<slug:slug>/", tour_inquiry_create_view, name="tour_create")

]