from django.shortcuts import redirect, render, get_object_or_404

from .forms import InquiryForm
from .models import Inquiry
from .services import create_inquiry
from catalog.models import Tour


def inquiry_create_view(request):
    if request.method == "POST":
        form = InquiryForm(data=request.POST)

        if form.is_valid():
            create_inquiry(form, Inquiry.Source.SELECTION, [])
            return redirect("inquiries:success")
    
    else:
        form = InquiryForm()

    return render(request, "inquiries/inquiry_form.html", {"form": form})

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
