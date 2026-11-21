from decimal import Decimal

from django import forms

from .models import Tour


class CatalogFilterForm(forms.Form):
    departure_from = forms.DateField(label="Вылет с", required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "form": "catalog-search"}))
    departure_to = forms.DateField(label="Вылет по", required=False, input_formats=["%Y-%m-%d"], widget=forms.DateInput(format="%Y-%m-%d", attrs={"type": "date", "form": "catalog-search"}))
    price_min = forms.DecimalField(label="Цена от", required=False, min_value=Decimal("0.01"), max_digits=16, decimal_places=2, widget=forms.NumberInput(attrs={"form": "catalog-search"}))
    price_max = forms.DecimalField(label="Цена до", required=False, min_value=Decimal("0.01"), max_digits=16, decimal_places=2, widget=forms.NumberInput(attrs={"form": "catalog-search"}))
    currency = forms.ChoiceField(label="Валюта", required=False, choices=[("", "Выберите валюту"), *Tour.Currency.choices], widget=forms.Select(attrs={"form": "catalog-search"}))
    price_basis = forms.ChoiceField(label="Цена указана", required=False, choices=[("", "Выберите вариант"), *Tour.PriceBasis.choices], widget=forms.Select(attrs={"form": "catalog-search"}))

    def clean(self):
        data = super().clean()
        departure_from = data.get("departure_from")
        departure_to = data.get("departure_to")
        price_min = data.get("price_min")
        price_max = data.get("price_max")

        if departure_from is not None and departure_to is not None and departure_to < departure_from:
            self.add_error("departure_to", "Дата окончания диапазона должна быть не раньше даты начала.")

        if price_min is not None or price_max is not None:
            if not data.get("currency") and not self.has_error("currency"):
                self.add_error("currency", "Выберите валюту для фильтра по цене.")
            if not data.get("price_basis") and not self.has_error("price_basis"):
                self.add_error("price_basis", "Укажите, за кого рассчитана цена.")

        if price_min is not None and price_max is not None and price_max < price_min:
            self.add_error("price_max", "Максимальная цена должна быть не меньше минимальной.")

        return data