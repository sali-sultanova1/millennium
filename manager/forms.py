from django import forms

from catalog.models import Destination, Tour

class TourDraftForm(forms.ModelForm):
    revision = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Tour
        fields = (
            "title", "destination", "resort", "hotel_name", "hotel_stars",
            "departure_city", "departure_date", "nights", "meal", "meal_details",
            "price", "currency", "price_basis", "price_details", "price_from", "short_description", "description",
        )

        widgets = {
            "departure_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "meal_details": forms.Textarea(attrs={"rows": 3}),
            "description": forms.Textarea(attrs={"rows": 5}),
        }

class DestinationForm(forms.ModelForm):
    class Meta:
        model = Destination
        fields = ("name", "image", "is_active")
        labels = {"name": "Название направления", "is_active": "Показывать на сайте"}