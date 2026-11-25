from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST, require_safe

from inquiries.models import Inquiry


@never_cache
@login_required(login_url="manager:login")
@permission_required("inquiries.view_inquiry", raise_exception=True)
@require_safe
def inquiry_status_view(request):
    return JsonResponse({"has_new": Inquiry.objects.filter(status=Inquiry.Status.NEW).exists()})


@never_cache
@login_required(login_url="manager:login")
@permission_required("inquiries.view_inquiry", raise_exception=True)
def inquiry_list_view(request):
    mine = request.GET.get("scope") == "mine"
    tabs = (("", "Все активные"), ("new", "Новые"), ("in_progress", "В работе"), ("closed", "Архив"))
    status = request.GET.get("status", "")

    if status not in Inquiry.Status.values:
        status = ""

    inquiries = Inquiry.objects.select_related("assigned_to")
    if status:
        inquiries = inquiries.filter(status=status)
    else:
        inquiries = inquiries.exclude(status=Inquiry.Status.CLOSED)

    if mine:
        inquiries = inquiries.filter(assigned_to=request.user)

    page_obj = Paginator(inquiries, 20).get_page(request.GET.get("page"))
    return render(request, "manager/inquiry_list.html", {"page_obj": page_obj, "mine": mine, "status": status, "tabs": tabs})

@never_cache
@login_required(login_url="manager:login")
@permission_required("inquiries.view_inquiry", raise_exception=True)
def inquiry_detail_view(request, pk):
    inquiries = Inquiry.objects.select_related("assigned_to").prefetch_related("selected_tours")
    inquiry = get_object_or_404(inquiries, pk=pk)
    return render(request, "manager/inquiry_detail.html", {"inquiry": inquiry})

@never_cache
@login_required(login_url="manager:login")
@permission_required(("inquiries.view_inquiry", "inquiries.change_inquiry"), raise_exception=True)
@require_POST
def inquiry_work_view(request, pk):
    inquiry = Inquiry.objects.filter(pk=pk)
    action = request.POST.get("action")

    if action == "claim":
        updated = inquiry.filter(assigned_to__isnull=True).exclude(
            status=Inquiry.Status.CLOSED
        ).update(assigned_to=request.user, status=Inquiry.Status.IN_PROGRESS)
        success = "Заявка взята в работу."
        failure = "Заявка уже назначена или закрыта."
    elif action == "close":
        updated = inquiry.filter(
            assigned_to=request.user, status=Inquiry.Status.IN_PROGRESS
        ).update(status=Inquiry.Status.CLOSED)
        success = "Заявка завершена и перенесена в архив."
        failure = "Закрыть можно только свою заявку со статусом «В работе»."
    else:
        return HttpResponseBadRequest("Неизвестное действие.")

    if updated:
        messages.success(request, success)
        if action == "close":
            return redirect(reverse(
                "manager:inquiry_list", query={"status": Inquiry.Status.CLOSED}
            ))
    elif not inquiry.exists():
        raise Http404
    else:
        messages.error(request, failure)

    return redirect("manager:inquiry_detail", pk=pk)

@never_cache
@login_required(login_url="manager:login")
@permission_required(("inquiries.view_inquiry", "inquiries.delete_inquiry"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def inquiry_delete_view(request, pk):
    archived = Inquiry.objects.filter(status=Inquiry.Status.CLOSED)

    if request.method == "POST":
        with transaction.atomic():
            inquiry = get_object_or_404(archived.select_for_update(), pk=pk)
            inquiry.delete()

        messages.success(request, "Заявка удалена.")
        return redirect(reverse("manager:inquiry_list", query={"status": Inquiry.Status.CLOSED}))

    inquiry = get_object_or_404(archived, pk=pk)
    return render(request, "manager/inquiry_delete.html", {"inquiry": inquiry})
