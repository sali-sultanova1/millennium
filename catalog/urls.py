from django.urls import path

from .views import tour_detail_view, tour_list_view


app_name = "catalog"

urlpatterns = [
    path("", tour_list_view, name="tour_list"),
    path("<slug:slug>/", tour_detail_view, name="tour_detail")
]