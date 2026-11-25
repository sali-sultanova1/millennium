
from django.contrib.auth.models import Group
from django.test import Client, TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import Destination, Tour
from inquiries.models import Inquiry

from .signals import MANAGERS_GROUP_NAME


class ManagerTourSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(username="tour-manager")
        cls.manager.groups.add(Group.objects.get(name=MANAGERS_GROUP_NAME))
        cls.egypt = Destination.objects.create(name="Египет", slug="egypt")
        cls.turkey = Destination.objects.create(name="Турция", slug="turkey")
        cls.published = Tour.objects.create(
            title="Reef retreat", slug="reef-retreat", destination=cls.egypt,
            resort="Шарм-эш-Шейх", hotel_name="Sea Garden", is_active=True,
        )
        cls.draft = Tour.objects.create(
            title="Reef weekend", slug="reef-weekend", destination=cls.egypt,
        )
        cls.other_direction = Tour.objects.create(
            title="Reef trip", slug="reef-trip", destination=cls.turkey, is_active=True,
        )

    def setUp(self):
        self.client.force_login(self.manager)
        self.url = reverse("manager:tour_list")

    def test_search_by_title_resort_and_hotel(self):
        for query in ("  RETREAT  ", "Шарм", "GARDEN"):
            with self.subTest(query=query):
                page = self.client.get(self.url, {"q": query})
                self.assertEqual(list(page.context["page_obj"]), [self.published])

    def test_direction_and_status_work_with_search(self):
        for status, tour in (("published", self.published), ("draft", self.draft)):
            with self.subTest(status=status):
                response = self.client.get(self.url, {
                    "q": "reef", "destination": "egypt", "status": status,
                })
                self.assertEqual(list(response.context["page_obj"]), [tour])
                self.assertContains(response, 'value="egypt" selected')

    def test_no_matches_offer_reset(self):
        response = self.client.get(self.url, {"q": "no match"})
        self.assertContains(response, "По этим условиям туров нет.")
        self.assertContains(response, f'href="{self.url}">Сбросить</a>')

    def test_status_and_pagination_links_preserve_filters(self):
        Tour.objects.bulk_create([
            Tour(title=f"Reef departure {index}", slug=f"reef-{index}",
                 destination=self.egypt, is_active=True)
            for index in range(20)
        ])
        filters = {"q": "reef", "destination": "egypt", "status": "published"}
        response = self.client.get(self.url, filters)
        self.assertEqual(response.context["page_obj"].paginator.count, 21)
        self.assertContains(response, "?q=reef&amp;destination=egypt&amp;status=published&amp;page=2")

        second_page = self.client.get(self.url, {**filters, "page": 2})
        self.assertContains(second_page, 'href="/manager/?q=reef&amp;destination=egypt&amp;status=draft"')


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
        dots_hidden = 'data-inquiry-dot aria-hidden="true" hidden'
        dots_visible = 'data-inquiry-dot aria-hidden="true">'
        tour_list = self.client.get(reverse("manager:tour_list"))
        self.assertContains(tour_list, url)
        self.assertContains(tour_list, dots_hidden)
        self.assertContains(self.client.get(reverse("manager:tour_create")), url)
        self.assertEqual(self.client.get(url).json(), {"has_new": False})

        inquiry = Inquiry.objects.create(
            name="Клиент", phone="0000000000", contact_method=Inquiry.ContactMethod.ANY,
            adults=1, children=0, source=Inquiry.Source.SELECTION,
        )
        response = self.client.get(url)
        self.assertEqual(response.json(), {"has_new": True})
        self.assertIn("no-store", response.headers["Cache-Control"])
        for page in ("manager:tour_list", "manager:destination_list", "manager:inquiry_list"):
            with self.subTest(page=page):
                self.assertContains(self.client.get(reverse(page)), dots_visible)

        self.client.post(reverse("manager:inquiry_work", args=[inquiry.pk]), {"action": "claim"})
        self.assertEqual(self.client.get(url).json(), {"has_new": False})
        self.assertContains(self.client.get(reverse("manager:inquiry_list")), dots_hidden)

    def test_new_inquiry_status_requires_inquiry_permission(self):
        url = reverse("manager:inquiry_status")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(User.objects.create_user(username="visitor"))
        self.assertEqual(self.client.get(url).status_code, 403)
