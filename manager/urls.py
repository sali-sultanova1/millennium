from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import employee_views, inquiry_views, views
from .forms import ManagerLoginForm

app_name = "manager"

urlpatterns = [
    path("", views.tour_list_view, name="tour_list"),
    path("tours/new/", views.tour_draft_view, name="tour_create"),
    path("tours/<int:pk>/edit/", views.tour_draft_view, name="tour_edit"),
    path("tours/<int:pk>/photos/<int:photo_pk>/delete/", views.tour_photo_delete_view, name="tour_photo_delete"),
    path("tours/<int:pk>/publication/", views.tour_publication_view, name="tour_publication"),
    path("directions/", views.destination_list_view, name="destination_list"),
    path("directions/new/", views.destination_form_view, name="destination_create"),
    path("directions/<int:pk>/edit/", views.destination_form_view, name="destination_edit"),
    path("directions/<int:pk>/delete/", views.destination_delete_view, name="destination_delete"),
    path("login/", LoginView.as_view(template_name="manager/login.html", authentication_form=ManagerLoginForm, next_page="manager:tour_list"), name="login"),
    path("logout/", LogoutView.as_view(next_page="manager:login"), name="logout"),
    path("profile/", employee_views.profile_view, name="profile"),
    path("tours/<int:pk>/delete/", views.tour_delete_view, name="tour_delete"),
    path("inquiries/", inquiry_views.inquiry_list_view, name="inquiry_list"),
    path("inquiries/status/", inquiry_views.inquiry_status_view, name="inquiry_status"),
    path("inquiries/<int:pk>/", inquiry_views.inquiry_detail_view, name="inquiry_detail"),
    path("inquiries/<int:pk>/work/", inquiry_views.inquiry_work_view, name="inquiry_work"),
    path("inquiries/<int:pk>/delete/", inquiry_views.inquiry_delete_view, name="inquiry_delete"),
    path("employees/", employee_views.employees_view, name="employees"),
    path("employees/<int:pk>/edit/", employee_views.employee_edit_view, name="employee_edit"),
    path("employees/<int:pk>/access/", employee_views.employee_access_view, name="employee_access"),
    path("employees/<int:pk>/email/", employee_views.employee_email_view, name="employee_email"),
]
