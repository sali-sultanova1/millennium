from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import Destination, Tour

from .forms import DestinationForm, TourDraftForm, TourPhotoForm
from .tour_photos import order_tour_photos, remove_tour_photo, save_tour_photos


@never_cache
@login_required(login_url="manager:login")
@permission_required("catalog.view_tour", raise_exception=True)
def tour_list_view(request):
    tours = Tour.objects.select_related("destination").order_by("-updated_at", "-pk")
    status = request.GET.get("status", "")

    if status == "draft":
        tours = tours.filter(is_active=False)
    elif status == "published":
        tours = tours.filter(is_active=True, destination__is_active=True)

    page_obj = Paginator(tours, 20).get_page(request.GET.get("page"))
    return render(request, "manager/tour_list.html", {"page_obj": page_obj, "status": status})

@never_cache
@login_required(login_url="manager:login")
@permission_required("catalog.view_tour", raise_exception=True)
@require_http_methods(["GET", "POST"])
def tour_draft_view(request, pk=None):
    permission = "catalog.add_tour" if pk is None else "catalog.change_tour"
    if not request.user.has_perm(permission):
        raise PermissionDenied

    is_post = request.method == "POST"
    data = request.POST if is_post else None
    files = request.FILES if is_post else None

    with transaction.atomic():
        tour = None
        if pk is not None:
            tours = Tour.objects.select_for_update() if is_post else Tour.objects.all()
            tour = get_object_or_404(tours, pk=pk)

        revision = tour.updated_at.isoformat() if tour else ""
        form = TourDraftForm(data, files, instance=tour, initial={"revision": revision})
        photos = tour.images.all() if tour else []
        photo_forms = [
            (photo, TourPhotoForm(data, prefix=f"photo-{photo.pk}"))
            for photo in photos
        ]

        if is_post:
            photos_valid = all([photo_form.is_valid() for _, photo_form in photo_forms])
            if form.is_valid() and photos_valid:
                if tour and form.cleaned_data["revision"] != revision:
                    form.add_error(None, "Тур уже изменился. Откройте его заново, чтобы увидеть актуальные данные.")
                else:
                    try:
                        ordered_photos = order_tour_photos(
                            photo_forms, form.cleaned_data["photos"], form.cleaned_data["photo_order"]
                        )
                    except ValidationError as error:
                        form.add_error("photo_order", error)
                    else:
                        draft = form.save(commit=False)
                        if pk is None:
                            draft.slug = f"tour-{uuid4().hex}"
                        draft.save()
                        save_tour_photos(draft, photo_forms, ordered_photos)
                        return redirect("manager:tour_list")

    return render(request, "manager/tour_form.html", {"form": form, "tour": tour, "photo_forms": photo_forms})

@never_cache
@login_required(login_url="manager:login")
@permission_required(("catalog.view_tour", "catalog.change_tour"), raise_exception=True)
@require_POST
def tour_photo_delete_view(request, pk, photo_pk):
    with transaction.atomic():
        tour = get_object_or_404(Tour.objects.select_for_update(), pk=pk)
        if request.POST.get("revision") != tour.updated_at.isoformat():
            return JsonResponse(
                {"error": "Тур изменился. Откройте его заново перед удалением фото."},
                status=409,
            )

        photo = get_object_or_404(tour.images.all(), pk=photo_pk)
        remove_tour_photo(photo)
        tour.save(update_fields=["updated_at"])

    return JsonResponse({"revision": tour.updated_at.isoformat()})

@never_cache
@login_required(login_url="manager:login")
@permission_required(("catalog.view_tour", "catalog.change_tour"), raise_exception=True)
@require_POST
def tour_publication_view(request, pk):
    action = request.POST.get("action")
    if action not in ("publish", "unpublish"):
        return HttpResponseBadRequest("Неизвестное действие.")

    publish = action == "publish"
    with transaction.atomic():
        tour = get_object_or_404(Tour.objects.select_for_update(), pk=pk)

        if publish and not tour.destination.is_active:
            messages.error(request, "Тур можно опубликовать только в активном направлении.")
            return redirect("manager:tour_list")

        if tour.is_active != publish:
            tour.is_active = publish
            tour.save(update_fields=["is_active", "updated_at"])

    messages.success(request, "Тур опубликован." if publish else "Тур снят с публикации.")
    return redirect("manager:tour_list")


@never_cache
@login_required(login_url="manager:login")
@permission_required("catalog.view_destination", raise_exception=True)
def destination_list_view(request):
    page_obj = Paginator(Destination.objects.all(), 20).get_page(request.GET.get("page"))
    return render(request, "manager/destination_list.html", {"page_obj": page_obj})


@never_cache
@login_required(login_url="manager:login")
@permission_required("catalog.view_destination", raise_exception=True)
@require_http_methods(["GET", "POST"])
def destination_form_view(request, pk=None):
    permission = "catalog.add_destination" if pk is None else "catalog.change_destination"
    if not request.user.has_perm(permission):
        raise PermissionDenied

    is_post = request.method == "POST"
    with transaction.atomic():
        destination = None
        if pk is not None:
            destinations = Destination.objects.select_for_update() if is_post else Destination.objects.all()
            destination = get_object_or_404(destinations, pk=pk)

        form = DestinationForm(request.POST if is_post else None, request.FILES if is_post else None, instance=destination)
        if is_post and form.is_valid():
            item = form.save(commit=False)
            if pk is None:
                item.slug = f"direction-{uuid4().hex}"
            item.save()
            messages.success(request, "Направление сохранено.")
            return redirect("manager:destination_list")

    return render(request, "manager/destination_form.html", {"form": form, "destination": destination})

@never_cache
@login_required(login_url="manager:login")
@permission_required(("catalog.view_destination", "catalog.delete_destination"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def destination_delete_view(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            destination = get_object_or_404(Destination.objects.select_for_update(), pk=pk)
            try:
                destination.delete()
            except ProtectedError:
                messages.error(request, "К направлению привязаны туры. Его можно скрыть в форме редактирования.")
            else:
                messages.success(request, "Направление удалено.")

        return redirect("manager:destination_list")

    destination = get_object_or_404(Destination, pk=pk)
    return render(request, "manager/destination_delete.html", {"destination": destination, "has_tours": destination.tours.exists()})

@never_cache
@login_required(login_url="manager:login")
@permission_required(("catalog.view_tour", "catalog.delete_tour"), raise_exception=True)
@require_http_methods(["GET", "POST"])
def tour_delete_view(request, pk):
    if request.method == "POST":
        with transaction.atomic():
            tour = get_object_or_404(Tour.objects.select_for_update(), pk=pk)
            if request.POST.get("revision") != tour.updated_at.isoformat():
                messages.error(request, "Тур изменился. Проверьте его перед удалением.")
                return redirect("manager:tour_delete", pk=pk)

            try:
                tour.delete()
            except ProtectedError:
                messages.error(request, "На этот тур есть заявки. Вы можете снять его с публикации.")
            else:
                messages.success(request, "Тур удалён.")

        return redirect("manager:tour_list")

    tour = get_object_or_404(Tour, pk=pk)
    return render(request, "manager/tour_delete.html", {"tour": tour, "revision": tour.updated_at.isoformat()})
