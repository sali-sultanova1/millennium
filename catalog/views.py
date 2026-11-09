from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Tour

def tour_list_view(request):
    tours = Tour.objects.filter(is_active=True, destination__is_active=True).select_related("destination")
    paginator = Paginator(tours, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "catalog/tour_list.html", {"tours": page_obj.object_list, "page_obj": page_obj})

def tour_detail_view(request, slug):
    tour = get_object_or_404(Tour.objects.filter(is_active=True, destination__is_active=True).select_related("destination"), slug=slug)

    return render(request, "catalog/tour_detail.html", {"tour": tour})
    