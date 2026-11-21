from django.urls import path
from django.views.generic import TemplateView

app_name = "pages"

urlpatterns = [
    path("contacts/", TemplateView.as_view(template_name="pages/contacts.html"), name="contacts"),
    
]