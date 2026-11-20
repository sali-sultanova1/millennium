from django.shortcuts import redirect, render, get_object_or_404

from .forms import InquiryForm
from .models import Inquiry
from .services import create_inquiry
from catalog.models import Tour

from django.views.decorators.http import require_http_methods


def inquiry_create_view(request):
    selected_tours = []

    if request.method == "POST":
        form = InquiryForm(data=request.POST)
        raw_ids = request.POST.getlist("ids")
        ids = []
        invalid_selection = False

        for raw_id in raw_ids:
            try:
                tour_id = int(raw_id)
            except ValueError:
                invalid_selection = True
                continue

            if tour_id <= 0 or tour_id in ids:
                invalid_selection = True
                continue

            ids.append(tour_id)

        selected_tours = list(Tour.objects.filter(pk__in=ids, is_active=True, destination__is_active=True))

        if invalid_selection or len(selected_tours) != len(ids):
            form.add_error(None, "Проверьте выбор туров. Некоторые варианты недоступны или указаны повторно.")

        if form.is_valid():
            create_inquiry(form, Inquiry.Source.SELECTION, selected_tours)
            return redirect("inquiries:success")
    else:
        form = InquiryForm()

    context = {
        "form": form,
        "show_favorites_picker": True,
        "selected_tour_ids": [tour.pk for tour in selected_tours],
    }
    return render(request, "inquiries/inquiry_form.html", context)

def inquiry_success_view(request):
    return render(request, "inquiries/inquiry_success.html")

def tour_inquiry_create_view(request, slug):
    tour = get_object_or_404(Tour, slug=slug, is_active=True, destination__is_active=True)
    
    if request.method == "POST":
        form = InquiryForm(data=request.POST)
        if form.is_valid():
            create_inquiry(form, Inquiry.Source.TOUR, [tour])
            return redirect("inquiries:success")
    else:
        form = InquiryForm()

    return render(request, "inquiries/inquiry_form.html", {"form": form, "tour": tour})

@require_http_methods(["GET", "POST"])
def favorites_inquiry_create_view(request):
    if request.method == "POST":
        data = request.POST
    else:
        data = request.GET

    raw_ids = data.getlist("ids")

    try:
        ids = [int(raw_id) for raw_id in raw_ids]
    except ValueError:
        ids = []

    if (
        not ids 
        or any(not (0 < tour_id <= 2**63 - 1) for tour_id in ids)
        or len(ids) != len(set(ids))
    ):
        return render(request, "inquiries/form.html", {"selection_error": "Выберите хотя бы один тур в избранном и повторите попытку."}, status=400)

    selected_tours = list(Tour.objects.filter(pk__in=ids, is_active=True, destination__is_active=True))

    if len(selected_tours) != len(ids):
        return render(request, "inquiries/form.html", {"selection_error": "Один или несколько выбранных туров больше недоступны."}, status=400)

    if request.method == "POST":
        form = InquiryForm(request.POST)

        if form.is_valid():
            create_inquiry(form, Inquiry.Source.FAVORITES, selected_tours)
            return redirect("inquiries:success")
    else:
        form = InquiryForm()

    return render(request, "inquiries/form.html", {"form": form, "selected_tours": selected_tours})