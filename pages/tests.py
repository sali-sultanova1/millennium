from django.test import TestCase
from django.urls import reverse

from catalog.models import Destination, Tour


class AgencyPagesTests(TestCase):
    def test_agency_pages_open(self):
        for name, title in (
            ("contacts", "Контакты"),
            ("about", "О компании"),
            ("services", "Услуги"),
            ("directions", "Направления"),
        ):
            with self.subTest(page=name):
                response = self.client.get(reverse(f"pages:{name}"))
                self.assertContains(response, f"<h1>{title}</h1>", html=True)

    def test_office_and_manager_contacts(self):
        contacts = self.client.get(reverse("pages:contacts"))
        for text in (
            "Ставрополь, ул. 50 лет ВЛКСМ, 28А",
            "ТЦ «Милан», 3-й этаж, офис 1",
            "10:00–17:00",
            "11:00–16:00",
            "Галимат Султанова",
            'href="tel:+79993799515"',
            'href="https://wa.me/79633861818"',
            'href="https://t.me/galima_sultanova"',
        ):
            self.assertContains(contacts, text)

        for page in (contacts, self.client.get(reverse("home"))):
            self.assertContains(page, 'href="tel:+79633861818"')
            self.assertContains(page, 'href="mailto:gvoyage26@mail.ru"')

    def test_navigation_links_to_agency_pages(self):
        response = self.client.get(reverse("home"))
        for name, label in (
            ("about", "О компании"),
            ("services", "Услуги"),
            ("directions", "Направления"),
        ):
            with self.subTest(page=name):
                url = reverse(f"pages:{name}")
                self.assertContains(response, f'<a href="{url}">{label}</a>', count=3, html=True)
                active_page = self.client.get(url)
                self.assertContains(
                    active_page, f'<a href="{url}" aria-current="page">{label}</a>',
                    count=2, html=True,
                )

    def test_services_link_to_catalog_favorites_and_inquiry(self):
        response = self.client.get(reverse("pages:services"))
        for name, label in (
            ("catalog:tour_list", "Открыть каталог"),
            ("catalog:favorites", "Перейти в избранное"),
            ("inquiries:create", "Оставить заявку"),
        ):
            with self.subTest(target=name):
                self.assertContains(response, f'href="{reverse(name)}">{label}</a>')

    def test_directions_empty_state(self):
        response = self.client.get(reverse("pages:directions"))
        self.assertContains(response, "Направления скоро появятся")
        self.assertContains(
            response, f'href="{reverse("inquiries:create")}">Оставить пожелания</a>'
        )

    def test_active_directions_link_to_filtered_catalog(self):
        turkey = Destination.objects.create(name="Турция", slug="turkey")
        china = Destination.objects.create(name="Китай", slug="china")
        Destination.objects.create(name="Непубличное направление", slug="hidden", is_active=False)
        tour = Tour.objects.create(destination=turkey, title="Анталья", slug="antalya", is_active=True)
        Tour.objects.create(destination=china, title="Шанхай", slug="shanghai", is_active=True)

        response = self.client.get(reverse("pages:directions"))
        catalog_url = reverse("catalog:tour_list")
        self.assertContains(response, f'href="{catalog_url}?destination=turkey"')
        self.assertContains(response, f'href="{catalog_url}?destination=china"')
        self.assertNotContains(response, "Непубличное направление")

        filtered = self.client.get(f"{catalog_url}?destination=turkey")
        self.assertQuerySetEqual(filtered.context["tours"], [tour])
