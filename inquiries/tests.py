from django.test import TestCase

from .forms import InquiryForm
from .models import Inquiry


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
        for ages in ("18", "три", "3,, 10"):
            with self.subTest(ages=ages):
                self.data["children_ages"] = ages
                form = InquiryForm(data=self.data)

                self.assertFalse(form.is_valid())
                self.assertIn("children_ages", form.errors)

    def test_children_age_with_trailing_comma_is_valid(self):
        self.data["children"] = 1
        self.data["children_ages"] = "3,"

        form = InquiryForm(data=self.data)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["children_ages"], "3")



