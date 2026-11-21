from django import template
from django.templatetags.static import static

register = template.Library()

DESTINATION_PHOTOS = {
    "китай": "china", "china": "china",
    "турция": "turkey", "turkey": "turkey",
    "египет": "egypt", "egypt": "egypt",
    "мальдивы": "maldives", "maldives": "maldives",
    "таиланд": "thailand", "тайланд": "thailand", "thailand": "thailand",
    "оаэ": "uae", "объединённые арабские эмираты": "uae", "uae": "uae",
    "дубай": "dubai", "dubai": "dubai",
}


@register.filter
def destination_photo(destination, size="large"):
    name = destination.name.strip().casefold()
    key = DESTINATION_PHOTOS.get(name) or DESTINATION_PHOTOS.get(destination.slug.casefold())
    suffix = "-480" if size == "small" else ""
    return static(f"catalog/images/{key}{suffix}.webp") if key else ""

@register.filter
def tour_count(value):
    if value % 10 == 1 and value % 100 != 11:
        noun = "тур"
    elif 2 <= value % 10 <= 4 and not 12 <= value % 100 <= 14:
        noun = "тура"
    else:
        noun = "туров"
    return f"{value}\xa0{noun}"


@register.filter
def nights_label(value):
    last_digit = value % 10
    if 11 <= value % 100 <= 14:
        unit = "ночей"
    elif last_digit == 1:
        unit = "ночь"
    elif 2 <= last_digit <= 4:
        unit = "ночи"
    else:
        unit = "ночей"
    return f"{value}\xa0{unit}"
