from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.db import transaction
from django.urls import reverse

from .models import Inquiry, InquiryTour


def send_inquiry_notification(inquiry_id):
    path = reverse("manager:inquiry_detail", args=[inquiry_id])
    url = f"{settings.INQUIRY_NOTIFICATION_BASE_URL}{path}"
    EmailMessage(
        subject=f"Миллениум — новая заявка №{inquiry_id}",
        body=f"На сайте оставили новую заявку.\n\nОткрыть в кабинете менеджера\n{url}",
        bcc=settings.INQUIRY_NOTIFICATION_EMAILS,
    ).send()


def create_inquiry(form, source, tours):
    tours = list(tours)
    tour_count = len(tours)
    
    if source not in Inquiry.Source.values:
        raise ValidationError("Неизвестный источник заявки.")

    if source == Inquiry.Source.TOUR and tour_count != 1:
        raise ValidationError("Заявка на конкретный тур должна содержать ровно один тур.")

    if source == Inquiry.Source.FAVORITES and tour_count == 0:
        raise ValidationError("Выберите хотя бы один тур.")


    seen_tour_ids = set()

    for tour in tours:
        if tour.pk is None:
            raise ValidationError("Выбранный тур не сохранён.")

        if tour.pk in seen_tour_ids:
            raise ValidationError("Один тур нельзя добавить в заявку дважды.")

        if not tour.is_active or not tour.destination.is_active:
            raise ValidationError("Один из выбранных туров больше недоступен.")

        seen_tour_ids.add(tour.pk)

    with transaction.atomic():
        inquiry = form.save(commit=False)
        inquiry.source = source
        inquiry.save()

        for position, tour in enumerate(tours):
            InquiryTour.objects.create(
                inquiry=inquiry,
                tour=tour,
                position=position,
                title_snapshot=tour.title,
                destination_snapshot=tour.destination.name,
                resort_snapshot=tour.resort,
                hotel_name_snapshot=tour.hotel_name,
                hotel_stars_snapshot=tour.hotel_stars,
                departure_city_snapshot=tour.departure_city,
                departure_date_snapshot=tour.departure_date,
                nights_snapshot=tour.nights,
                meal_snapshot=tour.get_meal_display(),
                meal_details_snapshot=tour.meal_details,
                price_snapshot=tour.price,
                currency_snapshot=tour.currency,
                price_basis_snapshot=tour.get_price_basis_display(),
                price_details_snapshot=tour.price_details,
                price_from_snapshot=tour.price_from,
            )

        if settings.INQUIRY_NOTIFICATION_EMAILS:
            transaction.on_commit(lambda: send_inquiry_notification(inquiry.pk), robust=True)

    return inquiry
