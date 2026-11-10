from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from catalog.models import Tour


class Inquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        IN_PROGRESS = "in_progrss", "В работе"
        CLOSED = "closed", "Закрыта"

    class Source(models.TextChoices):
        TOUR = "tour", "Страница тура"
        FAVORITES = "favorites", "Избранное"
        SELECTION = "selection", "Подбор тура"

    class ContactMethod(models.TextChoices):
        ANY = "any", "Нет предпочтений"
        PHONE = "phone", "Звонок по телефону"
        TELEGRAM = "telegram", "Telegram"
        WHATSAPP = "whatsapp", "WhatsApp"
        MAX = "max", "MAX"
    
    name = models.CharField(max_length=100, verbose_name="Имя")
    phone = models.CharField(max_length=30, verbose_name="Телефон")
    contact_method = models.CharField(max_length=20, choices=ContactMethod.choices, verbose_name="Как с вами удобнее связаться?")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    preferred_destinations = models.CharField(max_length=250, blank=True, verbose_name="Желаемые направления")
    departure_city = models.CharField(max_length=100, blank=True, verbose_name="Желаемый город вылета")
    departure_date_from = models.DateField(null=True, blank=True, verbose_name="Вылет не раньше")
    departure_date_to = models.DateField(null=True, blank=True, verbose_name="Вылет не позже")
    nights_min = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name="Минимум ночей")
    nights_max = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name="Максимум ночей")
    adults = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name="Количество взрослых")
    children = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Количество детей")
    children_ages = models.CharField(max_length=100, blank=True, verbose_name="Возраст детей", help_text="Возраст на момент поездки, например: 3, 10")
    budget_max = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Бюджет до, на всех туристов")
    budget_currency = models.CharField(max_length=3, choices=Tour.Currency.choices, blank=True, verbose_name="Валюта бюджета")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW, verbose_name="Статус")
    source = models.CharField(max_length=20, choices=Source.choices, verbose_name="Источник заявки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        ordering = ["-created_at", "-pk"]
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f"Заявка №{self.pk} — {self.name}"


class InquiryTour(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name="selected_tours", verbose_name = "Заявка")
    tour = models.ForeignKey("catalog.Tour", on_delete=models.PROTECT, related_name="inquiry_items", verbose_name="Тур")

    title_snapshot = models.CharField(max_length=220, verbose_name="Название тура при отправке")
    destination_snapshot = models.CharField(max_length=100, verbose_name="Направление при отправке")
    resort_snapshot = models.CharField(max_length=100, blank=True, verbose_name="Курорт при отправке")
    hotel_name_snapshot = models.CharField(max_length=200, blank=True, verbose_name="Отель при отправке")
    hotel_stars_snapshot = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Звёздность отеля при отправке")
    departure_city_snapshot = models.CharField(max_length=100, blank=True, verbose_name="Город вылета при отправке")
    departure_date_snapshot = models.DateField(null=True, blank=True, verbose_name="Дата вылета при отправке")
    nights_snapshot = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Количество ночей при отправке")
    meal_snapshot = models.CharField(max_length=100, blank=True, verbose_name="Питание при отправке")
    meal_details_snapshot = models.TextField(blank=True, verbose_name="Подробности питания при отправке")
    price_snapshot = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, verbose_name="Цена при отправке")
    currency_snapshot = models.CharField(max_length=3, verbose_name="Валюта при отправке")
    price_basis_snapshot = models.CharField(max_length=100, blank=True, verbose_name="Основание цены при отправке")
    price_details_snapshot = models.CharField(max_length=250, blank=True, verbose_name="Условия цены при отправке")
    price_from_snapshot = models.BooleanField(default=False, verbose_name="Цена «от» при отправке")
    position = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name="Порядок в заявке")

    class Meta:
        ordering = ["position", "pk"]
        verbose_name = 'Выбранный тур'
        verbose_name_plural = 'Выбранные туры'
        constraints = [models.UniqueConstraint(fields=["inquiry", "tour"], name="unique_tour_per_inquiry")]

    def __str__(self):
        return self.title_snapshot