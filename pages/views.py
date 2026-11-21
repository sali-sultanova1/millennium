from django.shortcuts import render

from catalog.models import Destination


def directions_view(request):
    destinations = Destination.objects.filter(is_active=True)
    return render(request, "pages/directions.html", {"destinations": destinations})
