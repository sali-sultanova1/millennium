from django.core.paginator import Paginator
from django.db.models import Case, F, Q, When
from django.shortcuts import get_object_or_404, render

from .forms import CatalogFilterForm
from .models import Destination, Tour


def published_tours():
    return (
        Tour.objects.filter(is_active=True, destination__is_active=True)
        .select_related("destination")
        .prefetch_related("images")
    )


def search_options(tours):
    return {
        "destinations": Destination.objects.filter(is_active=True),
        "departure_cities": (
            tours.exclude(departure_city="").order_by("departure_city")
            .values_list("departure_city", flat=True).distinct()
        ),
        "durations": tours.order_by("nights").exclude(nights=None).values_list("nights", flat=True).distinct(),
        "meal_choices": Tour.MealType.choices,
    }


def tour_list_view(request):
    filter_form = CatalogFilterForm(request.GET)
    tours = published_tours().filter(
        Q(departure_date__isnull=True) | Q(departure_date__gte=filter_form.today)
    )
    context = search_options(tours)

    destination = request.GET.get("destination", "")
    meal = request.GET.get("meal", "")
    city = request.GET.get("city", "")
    nights = request.GET.get("nights", "")
    sort = request.GET.get("sort", "")

    if destination:
        tours = tours.filter(destination__slug=destination)
    if meal:
        tours = tours.filter(meal=meal)
    if city:
        tours = tours.filter(departure_city=city)
    if nights:
        if len(nights) <= 5 and nights.isascii() and nights.isdecimal() and 1 <= int(nights) <= 32767:
            tours = tours.filter(nights=int(nights))
        else:
            tours = tours.none()

    if filter_form.is_valid():
        data = filter_form.cleaned_data
        departure_from = data["departure_from"]
        departure_to = data["departure_to"]
        price_min = data["price_min"]
        price_max = data["price_max"]

        if departure_from is not None:
            tours = tours.filter(departure_date__gte=departure_from)
        if departure_to is not None:
            tours = tours.filter(departure_date__lte=departure_to)

        if price_min is not None or price_max is not None:
            tours = tours.filter(currency=data["currency"], price_basis=data["price_basis"])
            if price_min is not None:
                tours = tours.filter(price__gte=price_min)
            if price_max is not None:
                tours = tours.filter(price__lte=price_max)
    else:
        tours = tours.none()

    if sort == "date":
        tours = tours.order_by(F("departure_date").asc(nulls_last=True), *Tour._meta.ordering)
    elif sort == "title":
        tours = tours.order_by("title", "pk")

    page_obj = Paginator(tours, 12).get_page(request.GET.get("page"))
    context.update({
        "tours": page_obj.object_list,
        "page_obj": page_obj,
        "selected_destination": destination,
        "selected_meal": meal,
        "selected_city": city,
        "selected_nights": nights,
        "selected_sort": sort,
        "filter_form": filter_form,
        "has_filters": any((destination, meal, city, nights)) or filter_form.has_changed(),
    })
    return render(request, "catalog/tour_list.html", context)

def tour_detail_view(request, slug):
    tour = get_object_or_404(published_tours(), slug=slug)
    same_destination_first = Case(When(destination_id=tour.destination_id, then=0), default=1)
    related_tours = (
        published_tours().exclude(pk=tour.pk)
        .order_by(same_destination_first, *Tour._meta.ordering)[:2]
    )
    return render(request, "catalog/tour_detail.html", {"tour": tour, "related_tours": related_tours})


def favorites_view(request):
    return render(request, "catalog/favorites.html")


def favorites_items_view(request):
    ids = []
    for raw_id in request.GET.getlist("ids"):
        try:
            tour_id = int(raw_id)
        except ValueError:
            continue
        if 0 < tour_id <= 2**63 - 1:
            ids.append(tour_id)

    tours = published_tours().filter(pk__in=ids)
    return render(request, "catalog/favorites_items.html", {
        "tours": tours,
        "selection_mode": request.GET.get("mode") == "selection",
    })


def home_view(request):
    tours = published_tours()
    context = search_options(tours)
    context["tours"] = tours[:3]
    return render(request, "catalog/home.html", context)
