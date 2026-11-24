import logging
from functools import partial
from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import transaction

from catalog.models import TourImage

logger = logging.getLogger(__name__)


def delete_unused_photo(storage, name):
    if name and not TourImage.objects.filter(image=name).exists():
        storage.delete(name)


def order_tour_photos(photo_forms, uploads, order):
    photos = {
        f"saved-{photo.pk}": photo
        for photo, form in photo_forms
        if not form.cleaned_data["delete"]
    }
    photos.update({f"new-{index}": upload for index, upload in enumerate(uploads)})

    if order is None:
        return list(photos.values())

    if (
        not isinstance(order, list)
        or any(not isinstance(key, str) for key in order)
        or len(order) != len(photos)
        or set(order) != photos.keys()
    ):
        raise ValidationError("Порядок фотографий изменился. Проверьте галерею и сохраните тур снова.")

    return [photos[key] for key in order]


def save_tour_photos(tour, photo_forms, ordered_photos):
    for photo, form in photo_forms:
        if form.cleaned_data["delete"]:
            remove_tour_photo(photo)

    saved_files = []
    try:
        for index, item in enumerate(ordered_photos):
            if isinstance(item, TourImage):
                if item.sort_order != index:
                    item.sort_order = index
                    item.save(update_fields=["sort_order"])
                continue

            photo = TourImage(tour=tour, sort_order=index)
            filename = f"{uuid4().hex}{Path(item.name).suffix.lower()}"
            photo.image.save(filename, item, save=False)
            saved_files.append(photo.image)
            photo.save()
    except Exception:
        for file in saved_files:
            try:
                file.storage.delete(file.name)
            except Exception:
                logger.exception("Не удалось удалить файл после отмены загрузки: %s", file.name)
        raise

def remove_tour_photo(photo):
    remove_file = partial(delete_unused_photo, photo.image.storage, photo.image.name)
    photo.delete()
    transaction.on_commit(remove_file, robust=True)