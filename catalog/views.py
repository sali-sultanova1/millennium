from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Destination, Tour


def tour_list_view(request):
    tours = Tour.objects.filter(is_active=True, destination__is_active=True).select_related("destination").prefetch_related("images")
    destinations = Destination.objects.filter(is_active=True)
    selected_destination = request.GET.get("destination", "")
    selected_meal = request.GET.get("meal", "")
    
    if selected_destination:
        tours = tours.filter(destination__slug=selected_destination)
    
    if selected_meal:
        tours = tours.filter(meal=selected_meal)
    
    paginator = Paginator(tours, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "catalog/tour_list.html", {"tours": page_obj.object_list, "page_obj": page_obj, "destinations": destinations, "meal_choices": Tour.MealType.choices, "selected_destination": selected_destination, "selected_meal": selected_meal})

def tour_detail_view(request, slug):
    tour = get_object_or_404(Tour.objects.filter(is_active=True, destination__is_active=True).select_related("destination").prefetch_related("images"), slug=slug)

    return render(request, "catalog/tour_detail.html", {"tour": tour})

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

    tours = Tour.objects.filter(pk__in=ids, is_active=True, destination__is_active=True)

    return render(request, "catalog/favorites_items.html", {"tours": tours, "selection_mode": request.GET.get("mode") == "selection",})

def home_view(request):
    destinations = Destination.objects.filter(is_active=True).order_by("sort_order", "name")

    tours = (Tour.objects.filter(is_active=True, destination__is_active=True).select_related("destination").order_by("-pk")[:6])

    return render(request, "catalog/home.html", {"destinations": destinations, "tours": tours})
