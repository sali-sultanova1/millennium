from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
    UsernameField,
)
from django.core.validators import MaxLengthValidator
from django.db.models import Q

from accounts.models import User
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


class ManagerLoginForm(AuthenticationForm):
    error_messages = {**AuthenticationForm.error_messages, "invalid_login": "Проверьте логин или почту и пароль."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        identifier = self.fields["username"]
        identifier.label = "Логин или электронная почта"
        identifier.max_length = User._meta.get_field("email").max_length
        identifier.widget.attrs.update({"maxlength": identifier.max_length, "autocomplete": "username"})
        identifier.validators.append(MaxLengthValidator(identifier.max_length))

    def clean(self):
        identifier = self.cleaned_data.get("username")
        if identifier and "@" in identifier and not User.objects.filter(username=identifier).exists():
            username = User.objects.filter(email__iexact=identifier).values_list("username", flat=True).first()
            if username is not None:
                self.cleaned_data["username"] = username

        return super().clean()


def clean_employee_username(username, employee_pk=None):
    other_users = User.objects.exclude(pk=employee_pk)
    if other_users.filter(username__iexact=username).exists():
        raise forms.ValidationError("Сотрудник с таким логином уже существует.")
    if "@" in username and other_users.filter(email__iexact=username).exists():
        raise forms.ValidationError("Этот логин уже используется как электронная почта.")
    return username


def clean_employee_email(email, employee_pk=None):
    other_users = User.objects.exclude(pk=employee_pk)
    if other_users.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
        raise forms.ValidationError("Этот адрес уже используется.")
    return email


class EmployeeEmailForm(forms.ModelForm):
    email = forms.EmailField(label="Электронная почта", max_length=254)

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        return clean_employee_email(self.cleaned_data["email"], self.instance.pk)


class EmployeeDetailsForm(EmployeeEmailForm):
    class Meta(EmployeeEmailForm.Meta):
        fields = ("username", "email", "phone", "first_name", "last_name")
        labels = {"username": "Логин", "first_name": "Имя", "last_name": "Фамилия"}
        field_classes = {"username": UsernameField}
        widgets = {"phone": forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"})}

    def clean_username(self):
        return clean_employee_username(self.cleaned_data["username"], self.instance.pk)


class EmployeeCreationForm(UserCreationForm):
    email = forms.EmailField(label="Электронная почта", max_length=254)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = EmployeeDetailsForm.Meta.fields
        labels = EmployeeDetailsForm.Meta.labels
        widgets = EmployeeDetailsForm.Meta.widgets

    def clean_username(self):
        return clean_employee_username(self.cleaned_data["username"])

    def clean_email(self):
        return clean_employee_email(self.cleaned_data["email"])
