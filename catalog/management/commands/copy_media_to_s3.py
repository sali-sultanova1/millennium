from hashlib import file_digest

from django.conf import settings
from django.core.files.storage import FileSystemStorage, storages
from django.core.management.base import BaseCommand, CommandError

from catalog.models import Destination, TourImage


class Command(BaseCommand):
    help = "Копирует фото туров и направлений из локального media в Object Storage."

    def handle(self, *args, **options):
        if not settings.MEDIA_USE_S3:
            raise CommandError("Запустите команду с MEDIA_USE_S3=True.")

        local = FileSystemStorage(location=settings.MEDIA_ROOT)
        bucket = storages["default"]
        directions = Destination.objects.exclude(image="").values_list("image", flat=True)
        tours = TourImage.objects.exclude(image="").values_list("image", flat=True)
        names = set(directions) | set(tours)

        copied_count = 0
        for name in sorted(names):
            exists_in_bucket = bucket.exists(name)
            if not local.exists(name):
                if exists_in_bucket:
                    continue
                raise CommandError(f"Файл отсутствует в media и в бакете: {name}")

            with local.open(name, "rb") as source:
                expected = file_digest(source, "sha256").digest()
                if not exists_in_bucket:
                    source.seek(0)
                    copied_name = bucket.save(name, source)
                    if copied_name != name:
                        raise CommandError(f"Бакет сохранил файл под другим ключом: {copied_name}")
                    copied_count += 1

            with bucket.open(name, "rb") as uploaded:
                actual = file_digest(uploaded, "sha256").digest()
            if actual != expected:
                raise CommandError(f"Содержимое файла в бакете отличается от локального: {name}")

        self.stdout.write(self.style.SUCCESS(
            f"Готово. Фото в бакете: {len(names)}. Скопировано за запуск: {copied_count}."
        ))