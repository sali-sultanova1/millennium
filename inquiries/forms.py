from django import forms

from .models import Inquiry

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = (
            "name",
            "phone",
            "preferred_destinations",
            "departure_city",
            "departure_date_from",
            "departure_date_to",
            "nights_min",
            "nights_max",
            "adults",
            "children",
            "children_ages",
            "budget_max",
            "budget_currency",
            "comment",
            "contact_method",
        )

        def clean_phone(self):
            phone = self.cleaned_data["phone"]
            allowed_characters = "0123456789+() -"

            for character in phone:
                if character not in allowed_characters:
                    raise forms.ValidationError(
                        "Введите корректный номер телефона."
                    )

            if "+" in phone:
                if phone.count("+") != 1 or not phone.startswith("+"):
                    raise forms.ValidationError(
                        "Введите корректный номер телефона."
                    )

            digits_count = 0

            for character in phone:
                if character.isdigit():
                    digits_count += 1

            if not 7 <= digits_count <= 15:
                raise forms.ValidationError(
                    "Введите корректный номер телефона."
                )

            return phone

        def clean(self):
            cleaned_data = super().clean()

            date_from = cleaned_data.get("departure_date_from")
            date_to = cleaned_data.get("departure_date_to")
            nights_min = cleaned_data.get("nights_min")
            nights_max = cleaned_data.get("nights_max")
            budget = cleaned_data.get("budget_max")
            currency = cleaned_data.get("budget_currency")
            children_ages = cleaned_data.get("children_ages", "")

            if date_from is not None and date_to is not None:
                if date_to < date_from:
                    self.add_error(
                        "departure_date_to",
                        "Конечная дата не может быть раньше начальной.",
                    )

            if nights_min is not None and nights_max is not None:
                if nights_max < nights_min:
                    self.add_error(
                        "nights_max",
                        "Максимум ночей не может быть меньше минимума.",
                    )

            if budget is not None and not currency:
                self.add_error(
                    "budget_currency",
                    "Выберите валюту бюджета.",
                )

            if children_ages:
                ages = children_ages.split(",")

                for age in ages:
                    age = age.strip()

                    if not age or not all(character in "0123456789" for character in age):
                        self.add_error(
                            "children_ages",
                            "Укажите возраст цифрами через запятую, например: 3, 10.",
                        )
                        break

                    if not 0 <= int(age) <= 17:
                        self.add_error(
                            "children_ages",
                            "Укажите возраст детей от 0 до 17 лет.",
                        )
                        break
            return cleaned_data