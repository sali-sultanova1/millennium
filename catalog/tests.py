from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase

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
        self.tour.departure_date = None
        self.tour.nights = None
        self.tour.hotel_stars = None
        self.tour.meal = ""

        self.tour.full_clean()


class CatalogRelationsTests(TestCase):
    def setUp(self):
        self.destination = Destination.objects.create(name="Китай", slug="china")
        self.tour = Tour.objects.create(destination=self.destination, title="Тестовый тур", slug="test-tour")

    def test_destination_with_tour_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.destination.delete()

        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())
        self.assertTrue(Tour.objects.filter(pk=self.tour.pk).exists())

    def test_images_are_ordered_by_sort_order_then_pk(self):
        last_image = TourImage.objects.create(tour=self.tour, image="tours/test-last.jpg", sort_order=10)
        first_image = TourImage.objects.create(tour=self.tour, image="tours/test-first.jpg", sort_order=0)
        second_image = TourImage.objects.create(tour=self.tour, image="tours/test-second.jpg", sort_order=0)

        self.assertEqual(list(self.tour.images.all()), [first_image, second_image, last_image])

    def test_deleting_tour_deletes_image_records(self):
        image = TourImage.objects.create(tour=self.tour, image="tours/test-photo.jpg")
        image_pk = image.pk

        self.tour.delete()

        self.assertFalse(TourImage.objects.filter(pk=image_pk).exists())
        self.assertTrue(Destination.objects.filter(pk=self.destination.pk).exists())