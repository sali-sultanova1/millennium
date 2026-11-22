from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ManagerConfig(AppConfig):
    name = "manager"

    def ready(self):
        from .signals import ensure_manager_group

        for label in ("catalog", "inquiries"):
            post_migrate.connect(ensure_manager_group, sender=self.apps.get_app_config(label), dispatch_uid="manager.ensure_manager_group")