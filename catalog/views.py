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
    