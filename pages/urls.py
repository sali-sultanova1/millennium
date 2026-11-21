from django.urls import path
from django.views.generic import TemplateView

from .views import directions_view

app_name = "pages"

urlpatterns = [
    path("contacts/", TemplateView.as_view(template_name="pages/contacts.html"), name="contacts"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),
    path("services/", TemplateView.as_view(template_name="pages/services.html"), name="services"),
    path("directions/", directions_view, name="directions"),
]
