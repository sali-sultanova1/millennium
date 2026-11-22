from django.contrib.auth.models import Group, Permission


def ensure_manager_group(sender, using, **kwargs):
    codes = {
        "catalog": ("view_tour", "add_tour", "change_tour", "delete_tour", "view_destination", "add_destination", "change_destination", "delete_destination"),
        "inquiries": ("view_inquiry", "change_inquiry", "delete_inquiry"),
    }
    permissions = Permission.objects.using(using).filter(content_type__app_label=sender.label, codename__in=codes[sender.label])
    
    if not permissions:
        return

    group, _ = Group.objects.using(using).get_or_create(name="Менеджеры")
    group.permissions.add(*permissions)