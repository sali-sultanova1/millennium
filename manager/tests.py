
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from inquiries.models import Inquiry

from .signals import MANAGERS_GROUP_NAME


class ManagerTeamTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_superuser(username="owner")
        cls.employee = User.objects.create_user(username="employee", is_staff=True)
        cls.group = Group.objects.get(name=MANAGERS_GROUP_NAME)
        cls.employee.groups.add(cls.group)

    def test_owner_creates_manager_without_admin_permissions(self):
        self.client.force_login(self.owner)
        url = reverse("manager:employees")
        password = "A-unique-test-password-47"
        data = {
            "username": "new-manager",
            "first_name": "Амина",
            "password1": password,
            "password2": password,
            "is_staff": "on",
            "is_superuser": "on",
        }

        self.assertRedirects(self.client.post(url, data), url)
        employee = User.objects.get(username="new-manager")
        self.assertTrue(employee.check_password(password))
        self.assertTrue(employee.is_active)
        self.assertTrue(employee.has_perm("inquiries.view_inquiry"))
        self.assertFalse(employee.is_staff)
        self.assertFalse(employee.is_superuser)
        self.assertContains(self.client.get(url), "Амина")
        self.assertContains(self.client.post(url, data), 'id="id_username_error"')
        self.assertEqual(User.objects.filter(username="new-manager").count(), 1)

    def test_non_owner_cannot_list_or_create_employees(self):
        url = reverse("manager:employees")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.employee)
        self.assertNotContains(self.client.get(reverse("manager:tour_list")), url)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"username": "blocked"}).status_code, 403)
        self.assertFalse(User.objects.filter(username="blocked").exists())

    def test_creating_employee_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(reverse("manager:employees"), {"username": "blocked"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username="blocked").exists())

    def test_new_inquiry_badge_tracks_status(self):
        self.client.force_login(self.employee)
        url = reverse("manager:inquiry_status")
        self.assertContains(self.client.get(reverse("manager:tour_list")), url)
        self.assertContains(self.client.get(reverse("manager:tour_create")), url)
        self.assertEqual(self.client.get(url).json(), {"has_new": False})

        inquiry = Inquiry.objects.create(
            name="Клиент", phone="0000000000", contact_method=Inquiry.ContactMethod.ANY,
            adults=1, children=0, source=Inquiry.Source.SELECTION,
        )
        response = self.client.get(url)
        self.assertEqual(response.json(), {"has_new": True})
        self.assertIn("no-store", response.headers["Cache-Control"])

        self.client.post(reverse("manager:inquiry_work", args=[inquiry.pk]), {"action": "claim"})
        self.assertEqual(self.client.get(url).json(), {"has_new": False})

    def test_new_inquiry_status_requires_inquiry_permission(self):
        url = reverse("manager:inquiry_status")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(User.objects.create_user(username="visitor"))
        self.assertEqual(self.client.get(url).status_code, 403)
