from django import forms

from catalog.models import Destination, Tour


class MultipleImageInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleImageInput

    def clean(self, data, initial=None):
        clean_image = super().clean
        return [clean_image(upload, initial) for upload in data or []]


class TourPhotoForm(forms.Form):
    delete = forms.BooleanField(label="Удалить", required=False)

class TourDraftForm(forms.ModelForm):
    revision = forms.CharField(required=False, widget=forms.HiddenInput)
    photo_order = forms.JSONField(required=False, widget=forms.HiddenInput)
    photos = MultipleImageField(label="Добавить фотографии", required=False)
    
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
        widgets = {"image": forms.FileInput}
