from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Destination(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    slug = models.SlugField(max_length=120, unique=True, verbose_name="Адрес в URL")
    is_active = models.BooleanField(default=True, verbose_name="Активно?")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Направление"
        verbose_name_plural = "Направления" 

    def __str__(self):
        return self.name


class Tour(models.Model):
    class MealType(models.TextChoices):
        ROOM_ONLY = "RO", "Без питания"
        BREAKFAST = "BB", "Завтрак"
        HALF_BOARD = "HB", "Полупансион"
        FULL_BOARD = "FB", "Полный пансион"
        ALL_INCLUSIVE = "AI", "Всё включено"
        ULTRA_ALL_INCLUSIVE = "UAI", "Ультра всё включено"
    
    class PriceBasis(models.TextChoices):
        PER_PERSON = "person", "За человека"
        TOTAL = "total", "За указанный состав туристов"
    
    class Currency(models.TextChoices):
        RUB = "RUB", "Российский рубль"
        USD = "USD", "Доллар США"
        EUR = "EUR", "Евро"
        KZT = "KZT", "Казахстанский тенге"
        BYN = "BYN", "Белорусский рубль"
        AMD = "AMD", "Армянский драм"
        AZN = "AZN", "Азербайджанский манат"
        KGS = "KGS", "Кыргызский сом"
        UZS = "UZS", "Узбекский сум"
        TJS = "TJS", "Таджикский сомони"
        TMT = "TMT", "Туркменский манат"
        MDL = "MDL", "Молдавский лей"
        GEL = "GEL", "Грузинский лари"
        UAH = "UAH", "Украинская гривна"
        AED = "AED", "Дирхам ОАЭ"
        TRY = "TRY", "Турецкая лира"
        CNY = "CNY", "Китайский юань"
        
    destination = models.ForeignKey(Destination, on_delete=models.PROTECT, related_name="tours", verbose_name="Направление")
    title = models.CharField(max_length=220, verbose_name="Название")
    slug = models.SlugField(max_length=220, unique=True, verbose_name="Адрес в URL")
    resort = models.CharField(max_length=100, blank=True, verbose_name="Курорт")
    hotel_name = models.CharField(max_length=200, blank=True, verbose_name="Название отеля")
    short_description = models.CharField(max_length=300, blank=True, verbose_name="Краткое описание")
    description = models.TextField(blank=True, verbose_name="Описание")
    departure_city = models.CharField(max_length=100, blank=True, verbose_name="Город вылета")
    departure_date = models.DateField(null=True, blank=True, verbose_name="Дата вылета")
    nights = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1)], verbose_name="Количество ночей")
    hotel_stars = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Звезды отеля")
    meal = models.CharField(max_length=3, choices=MealType.choices, blank=True, default="", verbose_name="Питание")
    meal_details = models.TextField(blank=True, verbose_name="Подробности питания")
    price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal("0.01"))], verbose_name="Цена")
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.RUB, verbose_name="Валюта")
    price_basis = models.CharField(max_length=10, choices=PriceBasis.choices, blank=True, verbose_name="Цена указана")
    price_details = models.CharField(max_length=250, blank=True, verbose_name="Условия цены")
    price_from = models.BooleanField(default=False, verbose_name="Цена от")
    is_active = models.BooleanField(default=False, verbose_name="Опубликован")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата изменения")
    

    class Meta:
        verbose_name = "Тур"
        verbose_name_plural = "Туры"
        ordering = ["sort_order", "-created_at", "-pk"]

    def clean(self):
        super().clean()
        errors = {}

        if self.price is not None:
            if not self.price_basis:
                errors["price_basis"] = "Укажите, за кого рассчитана цена."

            if (
                self.price_basis == self.PriceBasis.TOTAL and not self.price_details.strip()
            ):
                errors["price_details"] = (
                    "Укажите состав туристов, за который рассчитана цена."
                )

        elif self.price_from:
            errors["price_from"] = (
                "Для отметки «Цена от» необходимо указать цену."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class TourImage(models.Model):
    tour = models.ForeignKey(Tour, on_delete=models.CASCADE, related_name="images", verbose_name="Тур")
    image = models.ImageField(upload_to="tours/%Y/%m/", verbose_name="Фотография")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Описание изображения")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок отображения")

    class Meta:
        ordering = ["sort_order", "pk"]
        verbose_name = "Фотография тура"
        verbose_name_plural = "Фотографии туров"
            
    def __str__(self):
        return f"Фото: {self.tour.title}"
