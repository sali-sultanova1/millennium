from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import Destination, Tour, TourImage


class TourValidationTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Китай", slug="china")
        self.tour = Tour(destination=self.destination, title="Тестовый тур", slug="test-tour", nights=6, hotel_stars=4, price=Decimal("260000.00"), currency=Tour.Currency.RUB, price_basis=Tour.PriceBasis.TOTAL, price_details="За 2 взрослых")

    def test_total_price_with_details_is_valid(self):
        self.tour.full_clean()

    def test_price_requires_basis(self):
        self.tour.price_basis = ""

        with self.assertRaises(ValidationError) as context:
            self.tour.full_clean()

        self.assertIn("price_basis", context.exception.message_dict)

    def test_total_price_requires_details(self):
        for details in ("", "   "):
            with self.subTest(details=details):
                self.tour.price_details = details

                with self.assertRaises(ValidationError) as context:
                    self.tour.full_clean()

                self.assertIn("price_details", context.exception.message_dict)

    def test_per_person_price_is_valid(self):
        self.tour.price = Decimal("130000.00")
        self.tour.price_basis = Tour.PriceBasis.PER_PERSON
        self.tour.price_details = ""

        self.tour.full_clean()

    def test_price_on_request_is_valid(self):
        self.tour.price = None
        self.tour.price_basis = ""
        self.tour.price_details = ""
        self.tour.price_from = False

        self.tour.full_clean()

    def test_price_from_requires_price(self):
        self.tour.price = None
        self.tour.price_from = True

        with self.assertRaises(ValidationError) as context:
            self.tour.full_clean()

        self.assertIn("price_from", context.exception.message_dict)

    def test_price_from_with_price_is_valid(self):
        self.tour.price_from = True

        self.tour.full_clean()

    def test_price_must_be_positive(self):
        for price in (Decimal("0.00"), Decimal("-0.01")):
            with self.subTest(price=price):
                self.tour.price = price

                with self.assertRaises(ValidationError) as context:
                    self.tour.full_clean()

                self.assertIn("price", context.exception.message_dict)

    def test_minimum_price_is_valid(self):
        self.tour.price = Decimal("0.01")

        self.tour.full_clean()

    def test_currency_is_required(self):
        self.tour.currency = ""

        with self.assertRaises(ValidationError) as context:
            self.tour.full_clean()

        self.assertIn("currency", context.exception.message_dict)

    def test_nights_must_be_positive(self):
        self.tour.nights = 0

        with self.assertRaises(ValidationError) as context:
            self.tour.full_clean()

        self.assertIn("nights", context.exception.message_dict)

    def test_one_night_is_valid(self):
        self.tour.nights = 1

        self.tour.full_clean()

    def test_hotel_stars_outside_range_are_invalid(self):
        for stars in (0, 6):
            with self.subTest(stars=stars):
                self.tour.hotel_stars = stars

                with self.assertRaises(ValidationError) as context:
                    self.tour.full_clean()

                self.assertIn("hotel_stars", context.exception.message_dict)

    def test_hotel_star_boundaries_are_valid(self):
        for stars in (1, 5):
            with self.subTest(stars=stars):
                self.tour.hotel_stars = stars

                self.tour.full_clean()

    def test_optional_trip_details_can_be_empty(self):
        self.tour.departure_city = ""
        self.tour.departure_date = None
        self.tour.nights = None
        self.tour.hotel_name = ""
        self.tour.hotel_stars = None
        self.tour.resort = ""
        self.tour.meal = ""
        self.tour.meal_details = ""

        self.tour.full_clean()


class CatalogRelationsTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Китай", slug="china")
        self.tour = Tour.objects.create(destination=self.destination, title="Тестовый тур", slug="test-tour")

    def test_destination_with_tour_cannot_be_deleted(self):
        self.assertRaises(ProtectedError, self.destination.delete)

        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())

    def test_images_are_ordered_by_sort_order_then_pk(self):
        last_image = TourImage.objects.create(tour=self.tour, image="tours/test-last.jpg", sort_order=10)
        first_image = TourImage.objects.create(tour=self.tour, image="tours/test-first.jpg", sort_order=0)
        second_image = TourImage.objects.create(tour=self.tour, image="tours/test-second.jpg", sort_order=0)

        self.assertEqual(list(self.tour.images.all()), [first_image, second_image, last_image])

    def test_deleting_tour_deletes_image_records(self):
        tour_pk = self.tour.pk
        image = TourImage.objects.create(tour=self.tour, image="tours/test-photo.jpg")
        image_pk = image.pk

        self.tour.delete()

        self.assertFalse(Tour.objects.filter(pk=tour_pk).exists())
        self.assertFalse(TourImage.objects.filter(pk=image_pk).exists())
        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())


class CatalogViewsTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Китай", slug="china", is_active=True)
        self.tour = Tour.objects.create(destination=self.destination, title="Тестовый тур", slug="test-tour", is_active=True)

    def test_tour_list_shows_published_tour(self):
        url = reverse("catalog:tour_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/tour_list.html")
        self.assertContains(response, self.tour.title)

    def test_tour_list_hides_unpublished_tour(self):
        self.tour.is_active = False
        self.tour.save()
        url = reverse("catalog:tour_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.tour.title)

    def test_tour_list_hides_inactive_destination(self):
        self.destination.is_active = False
        self.destination.save()
        url = reverse("catalog:tour_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, self.tour.title)

    def test_tour_detail_shows_published_tour(self):
        url = reverse("catalog:tour_detail", kwargs={"slug": self.tour.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tour.title)
        self.assertTemplateUsed(response, "catalog/tour_detail.html")

    def test_tour_detail_hides_unpublished_tour(self):
        self.tour.is_active = False
        self.tour.save()

        url = reverse("catalog:tour_detail", kwargs={"slug": self.tour.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_tour_detail_hides_inactive_destination(self):
        self.destination.is_active = False
        self.destination.save()

        url = reverse("catalog:tour_detail", kwargs={"slug": self.tour.slug})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_tour_detail_returns_404_for_unknown_slug(self):
        url = reverse("catalog:tour_detail", kwargs={"slug": "missing-tour"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_tour_list_paginates_by_twelve(self):
        for i in range(12):
            Tour.objects.create(
                destination=self.destination,
                title=f"Дополнительный тур {i}",
                slug=f"extra-tour-{i}",
                is_active=True,
            )
        
        url = reverse("catalog:tour_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tours"]), 12)
        self.assertTrue(response.context["page_obj"].has_next())

        response = self.client.get(url, {"page": 2})

        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["tours"]), 1)
        self.assertFalse(response.context["page_obj"].has_next())


class CatalogFilterTests(TestCase):
    def setUp(self):
        self.destination1 = Destination.objects.create(name="Китай", slug="china", is_active=True)
        self.destination2 = Destination.objects.create(name="Турция", slug="turkey", is_active=True)
        self.tour1 = Tour.objects.create(destination=self.destination1, title="Первый", slug="test-tour1", meal="BB", is_active=True)
        self.tour2 = Tour.objects.create(destination=self.destination1, title="Второй", slug="test-tour2", meal="AI", is_active=True)
        self.tour3 = Tour.objects.create(destination=self.destination2, title="Третий", slug="test-tour3", meal="BB", is_active=True)

    def test_filter_by_destination(self):
        response = self.client.get(reverse("catalog:tour_list"), {"destination": "china"})

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["tours"], [self.tour1, self.tour2])

    def test_filter_by_meal(self):
        response = self.client.get(reverse("catalog:tour_list"), {"meal": "BB"})

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["tours"], [self.tour1, self.tour3])

    def test_filters_work_together(self):
        response = self.client.get(reverse("catalog:tour_list"), {"destination": "china", "meal": "BB"})

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["tours"], [self.tour1])

    def test_unknown_destination_returns_empty_list(self):
        response = self.client.get(reverse("catalog:tour_list"), {"destination": "missing"})

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["tours"], [])

    def test_unknown_meal_returns_empty_list(self):
        response = self.client.get(reverse("catalog:tour_list"), {"meal": "invalid"})

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.context["tours"], [])

    def test_inactive_destination_is_not_in_filter_choices(self):
        self.destination1.is_active = False
        self.destination1.save()

        response = self.client.get(reverse("catalog:tour_list"), {"destination": "china"})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.destination1, response.context["destinations"])
        self.assertIn(self.destination2, response.context["destinations"])
        self.assertCountEqual(response.context["tours"], [])

    def test_filtered_catalog_pagination(self):
        for i in range(12):
            Tour.objects.create(destination=self.destination1, title=f"Дополнительный тур {i}", slug=f"extra-tour-{i}", is_active=True, meal="BB")

        response = self.client.get(reverse("catalog:tour_list"), {"destination": "china", "meal": "BB", "page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 2)
        self.assertEqual(response.context["page_obj"].paginator.count, 13)
        self.assertEqual(len(response.context["tours"]), 1)
        self.assertFalse(response.context["page_obj"].has_next())
        self.assertTrue(response.context["page_obj"].has_previous())

        tour = response.context["tours"][0]
        self.assertEqual(tour.destination_id, self.destination1.pk)
        self.assertEqual(tour.meal, "BB")