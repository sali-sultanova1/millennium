from django.shortcuts import redirect, render

from .forms import InquiryForm
from .models import Inquiry
from .services import create_inquiry


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
