from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache


@never_cache
def csrf_failure(request, reason=""):
    match = request.resolver_match
    in_manager = match is not None and match.namespace == "manager"
    return_url = reverse("manager:tour_list" if in_manager else "home")
    return_label = "В кабинет" if in_manager else "На главную"

    if match and match.view_name in {
        "manager:destination_create",
        "manager:destination_edit",
        "manager:login",
        "manager:tour_create",
        "manager:tour_edit",
        "inquiries:create",
        "inquiries:tour_create",
    }:
        return_url = reverse(match.view_name, kwargs=match.kwargs)
        return_label = "Открыть форму заново"

    return render(
        request,
        "403.html",
        {
            "csrf_failed": True,
            "error_base": "manager/base.html" if in_manager else "base.html",
            "return_url": return_url,
            "return_label": return_label,
        },
        status=403,
    )
