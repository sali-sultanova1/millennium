from django.test import TestCase

from .forms import InquiryForm

from decimal import Decimal

from django.core.exceptions import ValidationError

from catalog.models import Destination, Tour

from .models import InquiryTour, Inquiry
from .services import create_inquiry

from unittest.mock import patch
from django.urls import reverse

from datetime import date


class InquiryFormTests(TestCase):
    def setUp(self):
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP}

    def test_valid_form(self):
        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_name_is_required(self):
        self.data["name"] = ""

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_phone_is_required(self):
        self.data["phone"] = ""

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("phone", form.errors)
    
    def test_contact_method_is_required(self):
        del self.data["contact_method"]

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("contact_method", form.errors)

    def test_unknown_contact_method_is_invalid(self):
        self.data["contact_method"] = "unknown"

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("contact_method", form.errors)
    
    def test_any_contact_method_is_valid(self):
        self.data["contact_method"] = Inquiry.ContactMethod.ANY

        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_phone_numbers(self):
        for number in ("abcdefg", "123456", "1234567890123456", "++79001234567", "7900+1234567"):
            with self.subTest(number=number):
                self.data["phone"] = number
                form = InquiryForm(data=self.data)

                self.assertFalse(form.is_valid())
                self.assertIn("phone", form.errors)

    def test_phone_length_boundaries_are_valid(self):
        for number in ("1234567", "123456789012345"):
            with self.subTest(number=number):
                self.data["phone"] = number
                form = InquiryForm(data=self.data)

                self.assertTrue(form.is_valid(), form.errors)

    def test_departure_date_to_before_from_is_invalid(self):
        self.data["departure_date_from"] = "2027-06-20"
        self.data["departure_date_to"] = "2027-06-10"
        
        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("departure_date_to", form.errors)

    def test_equal_departure_dates_are_valid(self):
        self.data["departure_date_from"] = "2027-06-20"
        self.data["departure_date_to"] = "2027-06-20"
        
        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)
  
    def test_nights_max_below_min_is_invalid(self):
        self.data["nights_min"] = "10"
        self.data["nights_max"] = "7"

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("nights_max", form.errors)

    def test_equal_nights_limits_are_valid(self):           
        self.data["nights_min"] = "7"
        self.data["nights_max"] = "7"

        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_budget_requires_currency(self):
        self.data["budget_max"] = "150000.00"
        self.data["budget_currency"] = ""

        form = InquiryForm(data=self.data)

        self.assertFalse(form.is_valid())
        self.assertIn("budget_currency", form.errors)
    
    def test_budget_with_currency_is_valid(self):
        self.data["budget_max"] = "150000.00"
        self.data["budget_currency"] = "RUB"  
     
        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_children_ages(self):
        self.data["children"] = "2"
        self.data["children_ages"] = "3, 10"

        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)
            
    def test_invalid_children_ages(self):
        for ages in ("18", "три", "3,, 10", ","):
            with self.subTest(ages=ages):
                self.data["children_ages"] = ages
                form = InquiryForm(data=self.data)

                self.assertFalse(form.is_valid())
                self.assertIn("children_ages", form.errors)

    def test_children_age_with_trailing_comma_is_valid(self):
        self.data["children"] = 1

        for ages in ("3,", "3,,", "3,,,"):
            with self.subTest(ages=ages):
                self.data["children_ages"] = ages
                form = InquiryForm(data=self.data)

                self.assertTrue(form.is_valid(), form.errors)
                self.assertEqual(form.cleaned_data["children_ages"], "3")


class InquiryServiceTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Китай", slug="china", is_active=True)
        self.tour = Tour.objects.create(destination=self.destination, title="Отдых в Китае", slug="holiday-in-china", is_active=True, price=Decimal("260000.00"), currency="RUB", price_basis=Tour.PriceBasis.PER_PERSON)
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP}

    def test_selection_without_tours_creates_inquiry(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        inquiry = create_inquiry(form, Inquiry.Source.SELECTION, [])

        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertEqual(inquiry.selected_tours.count(), 0)
        self.assertEqual(inquiry.name, self.data["name"])
        self.assertEqual(inquiry.phone, self.data["phone"])

    def test_tour_inquiry_creates_snapshot(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        inquiry = create_inquiry(form, Inquiry.Source.TOUR, [self.tour])

        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(inquiry.selected_tours.count(), 1)

        item = inquiry.selected_tours.get()

        self.assertEqual(inquiry.source, Inquiry.Source.TOUR)
        self.assertEqual(item.tour, self.tour)
        self.assertEqual(item.title_snapshot, "Отдых в Китае")
        self.assertEqual(item.destination_snapshot, "Китай")
        self.assertEqual(item.price_snapshot, Decimal("260000.00"))
        self.assertEqual(item.currency_snapshot, "RUB")
        self.assertEqual(item.price_basis_snapshot, "За человека")
        self.assertEqual(item.position, 0)

    def test_selection_with_tours_is_valid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        inquiry = create_inquiry(form, Inquiry.Source.SELECTION, [self.tour])

        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertEqual(inquiry.selected_tours.count(), 1)

        item = inquiry.selected_tours.get()

        self.assertEqual(item.tour, self.tour)

    def test_favorites_creates_one_inquiry_with_two_tours(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        second_tour = Tour.objects.create(destination=self.destination, title="Ещё один тур в Китай", slug="another-china-tour", is_active=True, price=Decimal("280000.00"), currency="RUB", price_basis=Tour.PriceBasis.PER_PERSON)

        inquiry = create_inquiry(form, Inquiry.Source.FAVORITES, [self.tour, second_tour])

        self.assertEqual(Inquiry.objects.count(), 1)
        self.assertEqual(inquiry.source, Inquiry.Source.FAVORITES)
        self.assertEqual(inquiry.selected_tours.count(), 2)
        self.assertEqual(list(inquiry.selected_tours.order_by("position").values_list("tour_id", flat=True)), [self.tour.pk, second_tour.pk])

    def test_unknown_source_is_invalid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        with self.assertRaises(ValidationError):
            create_inquiry(form, "unknown", [])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_tour_source_requires_one_tour(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.TOUR, [])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)
    
    def test_tour_source_rejects_multiple_tours(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        second_tour = Tour.objects.create(destination=self.destination, title="Ещё один тур в Китай", slug="another-china-tour", is_active=True, price=Decimal("280000.00"), currency="RUB", price_basis=Tour.PriceBasis.PER_PERSON)

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.TOUR, [self.tour, second_tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_favorites_requires_tours(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.FAVORITES, [])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_duplicate_tours_are_invalid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.FAVORITES, [self.tour, self.tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_inactive_tour_is_invalid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        self.tour.is_active = False
        self.tour.save()

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.TOUR, [self.tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_inactive_destination_is_invalid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        self.destination.is_active = False
        self.destination.save()

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.TOUR, [self.tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_unsaved_tour_is_invalid(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        unsaved_tour = Tour(destination=self.destination, title="Несохранённый тур", slug="unsaved-tour", is_active=True)

        with self.assertRaises(ValidationError):
            create_inquiry(form, Inquiry.Source.TOUR, [unsaved_tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)

    def test_snapshot_does_not_change_when_tour_changes(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        inquiry = create_inquiry(form, Inquiry.Source.TOUR, [self.tour])
        item = inquiry.selected_tours.get()
        
        self.tour.title = "Новое название тура"
        self.tour.price = Decimal("300000.00")
        self.tour.save()

        item.refresh_from_db()

        self.assertEqual(item.title_snapshot, "Отдых в Китае")
        self.assertEqual(item.price_snapshot, Decimal("260000.00"))

    def test_snapshot_failure_rolls_back_inquiry(self):
        form = InquiryForm(data=self.data)
        self.assertTrue(form.is_valid(), form.errors)

        with patch("inquiries.services.InquiryTour.objects.create", side_effect=RuntimeError("Ошибка сохранения снимка")):
            with self.assertRaises(RuntimeError):
                create_inquiry(form, Inquiry.Source.TOUR, [self.tour])

        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(InquiryTour.objects.count(), 0)


class InquiryViewTests(TestCase):
    def setUp(self):
        self.url = reverse("inquiries:create")
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP}

    def test_get_displays_empty_form(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inquiries/inquiry_form.html")
        self.assertFalse(response.context["form"].is_bound)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_valid_post_creates_inquiry(self):
        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("inquiries:success"))
        self.assertEqual(Inquiry.objects.count(), 1)
        
        inquiry = Inquiry.objects.get()

        self.assertEqual(inquiry.name, self.data["name"])
        self.assertEqual(inquiry.phone, self.data["phone"])
        self.assertEqual(inquiry.contact_method, self.data["contact_method"])
        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertEqual(inquiry.status, Inquiry.Status.NEW)
        self.assertEqual(inquiry.selected_tours.count(), 0)

    def test_invalid_post_does_not_create_inquiry(self):
        self.data["phone"] = "abcdefg"
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inquiries/inquiry_form.html")
        self.assertIn("phone", response.context["form"].errors)
        self.assertEqual(Inquiry.objects.count(), 0)
        self.assertEqual(response.context["form"]["name"].value(), self.data["name"])

    def test_post_cannot_override_source_or_status(self):
        self.data["source"] = Inquiry.Source.FAVORITES
        self.data["status"] = Inquiry.Status.CLOSED

        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("inquiries:success"))

        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertEqual(inquiry.status, Inquiry.Status.NEW)

    def test_success_page_does_not_create_inquiry(self):
        url = reverse("inquiries:success")

        for _ in range(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "inquiries/inquiry_success.html")

        self.assertEqual(Inquiry.objects.count(), 0)


class TourInquiryViewTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Турция", slug="turkey", is_active=True)
        self.tour = Tour.objects.create(destination=self.destination, title="Неделя в Анталье", slug="week-in-antalya", resort="Анталья", hotel_name="Test Hotel", short_description="Тур на семь ночей", description="Пляжный отдых в Анталье.", departure_city="Махачкала", departure_date=date(2027, 6, 15), nights=7, hotel_stars=4, meal="AI", price=Decimal("55000.00"), currency="RUB", price_basis=Tour.PriceBasis.PER_PERSON, is_active=True)
        self.url = reverse("inquiries:tour_create", kwargs={"slug": self.tour.slug})
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP}

    def test_get_displays_selected_tour(self):
        response = self.client.get(self.url)

        self.assertContains(response, self.tour.title, status_code=200)
        self.assertTemplateUsed(response, "inquiries/inquiry_form.html")
        self.assertEqual(response.context["tour"], self.tour)

    def test_valid_post_creates_tour_inquiry(self):
        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("inquiries:success"))
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.source, Inquiry.Source.TOUR)

        item = inquiry.selected_tours.get()
        self.assertEqual(item.tour_id, self.tour.pk)

    def test_inactive_tour_returns_404(self):
        self.tour.is_active = False
        self.tour.save(update_fields=["is_active"])

        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 404)
        self.assertFalse(Inquiry.objects.exists())

    def test_tour_in_inactive_destination_returns_404(self):
        self.destination.is_active = False
        self.destination.save(update_fields=["is_active"])

        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url, self.data).status_code, 404)
        self.assertFalse(Inquiry.objects.exists())

class FavoritesInquiryViewTests(TestCase):
    def setUp(self):
        destination = Destination.objects.create(name="Китай", slug="china", is_active=True)
        self.first_tour = Tour.objects.create(destination=destination, title="Путешествие в Пекин", slug="beijing-trip", is_active=True)
        self.second_tour = Tour.objects.create(destination=destination, title="Путешествие в Шанхай", slug="shanghai-trip", is_active=True)
        self.third_tour = Tour.objects.create(destination=destination, title="Путешествие в Гуанчжоу", slug="guangzhou-trip", is_active=True)

        self.url = reverse("inquiries:favorites_create")
        self.selected_ids = [self.first_tour.pk, self.third_tour.pk]
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP, "ids": self.selected_ids}

    def test_get_displays_selected_tours(self):
        response = self.client.get(self.url, {"ids": self.selected_ids})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "inquiries/inquiry_form.html")
        self.assertCountEqual(response.context["selected_tours"], [self.first_tour, self.third_tour])
        self.assertContains(response, self.first_tour.title)
        self.assertContains(response, self.third_tour.title)
        self.assertNotContains(response, self.second_tour.title)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_valid_post_creates_one_inquiry_with_selected_tours(self):
        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("inquiries:success"))

        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.source, Inquiry.Source.FAVORITES)

        saved_ids = inquiry.selected_tours.values_list("tour_id", flat=True)
        self.assertCountEqual(saved_ids, self.selected_ids)

    def test_invalid_phone_preserves_selected_tours(self):
        self.data["phone"] = "abcdefg"
        response = self.client.post(self.url, self.data)

        self.assertEqual(response.status_code, 200)
        self.assertIn("phone", response.context["form"].errors)
        self.assertCountEqual(response.context["selected_tours"], [self.first_tour, self.third_tour])
        self.assertContains(response, f'<input type="hidden" name="ids" value="{self.first_tour.pk}">', html=True)
        self.assertContains(response, f'<input type="hidden" name="ids" value="{self.third_tour.pk}">', html=True)
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_tour_hidden_after_get_prevents_inquiry_creation(self):
        response = self.client.get(self.url, {"ids": self.selected_ids})
        self.assertEqual(response.status_code, 200)

        self.third_tour.is_active = False
        self.third_tour.save()

        response = self.client.post(self.url, self.data)

        self.assertNotEqual(response.headers.get("Location"), reverse("inquiries:success"))
        self.assertEqual(Inquiry.objects.count(), 0)


class SelectionInquiryViewTests(TestCase):
    def setUp(self):
        destination = Destination.objects.create(name="Китай", slug="china", is_active=True)
        self.first_tour = Tour.objects.create(destination=destination, title="Пекин", slug="beijing", is_active=True)
        self.second_tour = Tour.objects.create(destination=destination, title="Шанхай", slug="shanghai", is_active=True)
        self.url = reverse("inquiries:create")
        self.data = {"name": "Анна", "phone": "+7 (900) 123-45-67", "contact_method": Inquiry.ContactMethod.WHATSAPP}

    def test_post_without_ids_creates_selection_inquiry_without_tours(self):
        response = self.client.post(self.url, self.data)

        self.assertRedirects(response, reverse("inquiries:success"))
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertEqual(inquiry.selected_tours.count(), 0)

    def test_post_with_two_active_tours_attaches_both_to_one_inquiry(self):
        selected_ids = [self.first_tour.pk, self.second_tour.pk]
        response = self.client.post(self.url, {**self.data, "ids": selected_ids})

        self.assertRedirects(response, reverse("inquiries:success"))
        inquiry = Inquiry.objects.get()
        self.assertEqual(inquiry.source, Inquiry.Source.SELECTION)
        self.assertCountEqual(inquiry.selected_tours.values_list("tour_id", flat=True), selected_ids)

    def test_post_with_hidden_tour_returns_form_error_without_creating_inquiry(self):
        self.second_tour.is_active = False
        self.second_tour.save(update_fields=["is_active"])
        selected_ids = [self.first_tour.pk, self.second_tour.pk]

        response = self.client.post(self.url, {**self.data, "ids": selected_ids})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].non_field_errors())
        self.assertEqual(Inquiry.objects.count(), 0)