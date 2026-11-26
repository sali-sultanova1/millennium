
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
        self.assertContains(response, f'href="{self.url}" data-tour-search-reset>Сбросить</a>')

    def test_search_markup_exposes_initial_result_count(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-tour-search-reset hidden')
        self.assertContains(response, 'data-tour-search-results data-result-count="3"')
        self.assertContains(response, "/static/manager/tour-search.js")

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
            "email": "amina@example.test",
            "phone": "+7 (900) 123-45-67",
            "first_name": "Амина",
            "password1": password,
            "password2": password,
            "is_staff": "on",
            "is_superuser": "on",
        }

        self.assertRedirects(self.client.post(url, data), url)
        employee = User.objects.get(username="new-manager")
        self.assertTrue(employee.check_password(password))
        self.assertEqual(employee.email, data["email"])
        self.assertEqual(employee.phone, data["phone"])
        self.assertTrue(employee.is_active)
        self.assertTrue(employee.has_perm("inquiries.view_inquiry"))
        self.assertFalse(employee.is_staff)
        self.assertFalse(employee.is_superuser)
        self.assertContains(self.client.get(url), "Амина")
        self.assertContains(self.client.get(url), data["email"])
        self.assertContains(self.client.post(url, data), 'id="id_username_error"')
        self.assertEqual(User.objects.filter(username="new-manager").count(), 1)

    def test_owner_must_supply_a_unique_employee_email(self):
        self.client.force_login(self.owner)
        self.owner.email = "owner@example.test"
        self.owner.save(update_fields=["email"])
        url = reverse("manager:employees")
        password = "A-unique-test-password-47"
        data = {"username": "new-manager", "phone": "+79001234567", "password1": password, "password2": password}

        for email in ("", "OWNER@example.test", "invalid"):
            with self.subTest(email=email):
                response = self.client.post(url, {**data, "email": email})
                self.assertContains(response, 'id="id_email_error"')
        self.assertFalse(User.objects.filter(username="new-manager").exists())

    def test_employee_phone_is_required_and_validated_on_creation(self):
        self.client.force_login(self.owner)
        url = reverse("manager:employees")
        password = "A-unique-test-password-47"
        data = {"username": "new-manager", "email": "new@example.test", "password1": password, "password2": password}
        for phone in ("", "12345", "invalid"):
            with self.subTest(phone=phone):
                self.assertContains(self.client.post(url, {**data, "phone": phone}), 'id="id_phone_error"')

        self.assertFalse(User.objects.filter(username="new-manager").exists())

    def test_owner_adds_email_to_existing_employee_and_both_logins_work(self):
        password = "A-unique-test-password-47"
        self.employee.set_password(password)
        self.employee.save(update_fields=["password"])
        login_url = reverse("manager:login")
        tour_list = reverse("manager:tour_list")

        legacy_client = Client()
        self.assertRedirects(legacy_client.post(login_url, {"username": self.employee.username, "password": password}), tour_list)

        self.client.force_login(self.owner)
        url = reverse("manager:employee_email", args=[self.employee.pk])
        self.assertContains(self.client.get(reverse("manager:employees")), reverse("manager:employee_edit", args=[self.employee.pk]))
        self.assertRedirects(self.client.post(url, {"email": "employee@example.test"}), reverse("manager:employees"))
        self.employee.refresh_from_db()
        self.assertEqual(self.employee.email, "employee@example.test")

        for identifier in (self.employee.username, "EMPLOYEE@EXAMPLE.TEST"):
            with self.subTest(identifier=identifier):
                client = Client()
                self.assertRedirects(client.post(login_url, {"username": identifier, "password": password}), tour_list)
                self.assertEqual(client.session["_auth_user_id"], str(self.employee.pk))

        self.employee.is_active = False
        self.employee.save(update_fields=["is_active"])
        client = Client()
        response = client.post(login_url, {"username": self.employee.email, "password": password})
        self.assertContains(response, "Проверьте логин или почту и пароль.", status_code=200)
        self.assertNotIn("_auth_user_id", client.session)

    def test_employee_cannot_edit_employee_email(self):
        self.client.force_login(self.employee)
        url = reverse("manager:employee_email", args=[self.employee.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {"email": "employee@example.test"}).status_code, 403)

    def test_legacy_owner_email_form_still_saves_email(self):
        self.client.force_login(self.owner)
        url = reverse("manager:employee_email", args=[self.owner.pk])
        self.assertContains(self.client.get(url), "Моя почта")
        self.assertRedirects(self.client.post(url, {"email": "owner@example.test"}), reverse("manager:employees"))
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.email, "owner@example.test")

    def test_owner_can_edit_own_profile(self):
        self.client.force_login(self.owner)
        url = reverse("manager:employee_edit", args=[self.owner.pk])
        employees_url = reverse("manager:employees")
        self.assertContains(self.client.get(employees_url), f'href="{url}">Мой профиль</a>')
        response = self.client.get(url)
        self.assertContains(response, "<h1>Мой профиль</h1>")
        self.assertNotContains(response, reverse("manager:employee_access", args=[self.owner.pk]))
        data = {
            "username": "new-owner-login",
            "email": "manager-owner@example.test",
            "phone": "+7 (900) 123-45-67",
            "first_name": "Амина",
            "last_name": "Саидова",
        }
        self.assertRedirects(self.client.post(url, data), employees_url)
        self.owner.refresh_from_db()
        for field, value in data.items():
            self.assertEqual(getattr(self.owner, field), value)
        self.assertTrue(self.owner.is_superuser)
        self.assertTrue(self.owner.is_active)
        self.assertEqual(self.client.session["_auth_user_id"], str(self.owner.pk))

    def test_employee_updates_own_account_and_owner_sees_new_details(self):
        employee_client = Client()
        employee_client.force_login(self.employee)
        url = reverse("manager:profile")
        self.client.force_login(self.owner)
        employees_url = reverse("manager:employees")
        self.assertContains(self.client.get(employees_url), "<strong>employee</strong>", html=True)
        tours = employee_client.get(reverse("manager:tour_list"))
        self.assertContains(tours, f'href="{url}">Мой профиль</a>')
        profile = employee_client.get(url)
        self.assertContains(profile, "<h1>Мой профиль</h1>", html=True)
        self.assertNotContains(profile, reverse("manager:employee_access", args=[self.employee.pk]))

        data = {
            "username": "updated-login",
            "email": "updated@example.test",
            "phone": "+7 (900) 123-45-67",
            "first_name": "Амина",
            "last_name": "Саидова",
        }
        response = employee_client.post(url, {**data, "pk": self.owner.pk, "is_superuser": "on"})
        self.assertRedirects(response, url)
        self.employee.refresh_from_db()
        self.owner.refresh_from_db()
        self.assertEqual(self.employee.username, data["username"])
        self.assertEqual(self.employee.email, data["email"])
        self.assertFalse(self.employee.is_superuser)
        self.assertEqual(self.owner.username, "owner")
        self.assertEqual(employee_client.session["_auth_user_id"], str(self.employee.pk))

        team = self.client.get(employees_url)
        for value in (*data.values(), "Амина Саидова"):
            self.assertContains(team, value)
        self.assertNotContains(team, "<strong>employee</strong>", html=True)

    def test_profile_requires_active_cabinet_access(self):
        url = reverse("manager:profile")
        login_url = reverse("manager:login")
        self.assertRedirects(self.client.get(url), f"{login_url}?next={url}")
        self.client.force_login(User.objects.create_user(username="visitor"))
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, {}).status_code, 403)

        self.client.force_login(self.employee)
        User.objects.filter(pk=self.employee.pk).update(is_active=False)
        self.assertRedirects(self.client.get(url), f"{login_url}?next={url}")

    def test_owner_cannot_edit_another_owner_profile(self):
        other = User.objects.create_superuser(username="another-owner")
        other.groups.add(self.group)
        self.client.force_login(self.owner)
        url = reverse("manager:employee_edit", args=[other.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, {"username": "attempted-edit"}).status_code, 404)

    def test_owner_can_edit_employee_details(self):
        self.client.force_login(self.owner)
        url = reverse("manager:employee_edit", args=[self.employee.pk])
        data = {
            "username": "renewed-login",
            "email": "new@example.test",
            "phone": "+7 (900) 123-45-67",
            "first_name": "Амина",
            "last_name": "Саидова",
            "is_active": "",
            "is_superuser": "on",
        }
        self.assertContains(self.client.post(url, {**data, "phone": ""}), 'id="id_phone_error"')
        self.assertRedirects(self.client.post(url, data), reverse("manager:employees"))
        self.employee.refresh_from_db()
        for field in ("username", "email", "phone", "first_name", "last_name"):
            self.assertEqual(getattr(self.employee, field), data[field])
        self.assertTrue(self.employee.is_active)
        self.assertFalse(self.employee.is_superuser)
        self.assertTrue(self.employee.groups.filter(pk=self.group.pk).exists())

    def test_disabling_employee_revokes_sessions_and_reenabling_allows_new_login(self):
        password = "A-unique-test-password-47"
        self.employee.set_password(password)
        self.employee.save(update_fields=["password"])
        already_open = Client()
        already_open.force_login(self.employee)
        idle = Client()
        idle.force_login(self.employee)

        self.client.force_login(self.owner)
        access_url = reverse("manager:employee_access", args=[self.employee.pk])
        edit_url = reverse("manager:employee_edit", args=[self.employee.pk])
        tour_list = reverse("manager:tour_list")
        login_url = reverse("manager:login")
        credentials = {"username": self.employee.username, "password": password}
        self.assertEqual(self.client.get(access_url).status_code, 405)
        self.assertRedirects(self.client.post(access_url, {"action": "disable"}), edit_url)
        self.assertContains(self.client.get(edit_url), "Включить доступ")
        self.assertRedirects(already_open.get(tour_list), f"{login_url}?next={tour_list}")
        self.assertContains(Client().post(login_url, credentials), "Проверьте логин или почту и пароль.")

        self.assertRedirects(self.client.post(access_url, {"action": "enable"}), edit_url)
        self.assertRedirects(idle.get(tour_list), f"{login_url}?next={tour_list}")
        self.assertRedirects(idle.post(login_url, credentials), tour_list)

    def test_access_control_requires_owner_and_rejects_owner_account(self):
        edit_url = reverse("manager:employee_edit", args=[self.employee.pk])
        access_url = reverse("manager:employee_access", args=[self.employee.pk])
        self.client.force_login(self.employee)
        self.assertEqual(self.client.get(edit_url).status_code, 403)
        self.assertEqual(self.client.post(access_url, {"action": "disable"}).status_code, 403)
        self.client.force_login(self.owner)
        owner_url = reverse("manager:employee_access", args=[self.owner.pk])
        self.assertEqual(self.client.post(owner_url, {"action": "disable"}).status_code, 404)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)

    def test_access_change_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        access_url = reverse("manager:employee_access", args=[self.employee.pk])
        self.assertEqual(client.post(access_url, {"action": "disable"}).status_code, 403)
        self.employee.refresh_from_db()
        self.assertTrue(self.employee.is_active)

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
        self.assertEqual(self.client.get(url).json(), {"has_new": False, "new_ids": []})

        inquiry = Inquiry.objects.create(
            name="Клиент", phone="0000000000", contact_method=Inquiry.ContactMethod.ANY,
            adults=1, children=0, source=Inquiry.Source.SELECTION,
        )
        response = self.client.get(url)
        self.assertEqual(response.json(), {"has_new": True, "new_ids": [str(inquiry.pk)]})
        self.assertIn("no-store", response.headers["Cache-Control"])
        for page in ("manager:tour_list", "manager:destination_list", "manager:inquiry_list"):
            with self.subTest(page=page):
                self.assertContains(self.client.get(reverse(page)), dots_visible)

        second = Inquiry.objects.create(
            name="Другой клиент", phone="0000000000", contact_method=Inquiry.ContactMethod.ANY,
            adults=1, children=0, source=Inquiry.Source.SELECTION,
        )
        self.assertEqual(self.client.get(url).json(), {"has_new": True, "new_ids": [str(inquiry.pk), str(second.pk)]})

        self.client.post(reverse("manager:inquiry_work", args=[inquiry.pk]), {"action": "claim"})
        self.assertEqual(self.client.get(url).json(), {"has_new": True, "new_ids": [str(second.pk)]})

        self.client.post(reverse("manager:inquiry_work", args=[second.pk]), {"action": "claim"})
        self.assertEqual(self.client.get(url).json(), {"has_new": False, "new_ids": []})
        self.assertContains(self.client.get(reverse("manager:inquiry_list")), dots_hidden)

    def test_new_inquiry_status_requires_inquiry_permission(self):
        url = reverse("manager:inquiry_status")
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(User.objects.create_user(username="visitor"))
        self.assertEqual(self.client.get(url).status_code, 403)
