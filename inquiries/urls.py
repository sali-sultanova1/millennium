from django.urls import path

from .views import inquiry_create_view, inquiry_success_view

app_name = "inquiries"

urlpatterns = [
    path("", inquiry_create_view, name="create"),
    path("success/", inquiry_success_view, name="success")
]