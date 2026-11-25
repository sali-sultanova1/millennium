from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from accounts.models import User

from .forms import EmployeeCreationForm
from .signals import MANAGERS_GROUP_NAME


@sensitive_post_parameters("password1", "password2")
@never_cache
@login_required(login_url="manager:login")
@require_http_methods(["GET", "POST"])
def employees_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    group = Group.objects.filter(name=MANAGERS_GROUP_NAME).first()
    employees = group.user_set.order_by("username") if group else User.objects.none()
    form = EmployeeCreationForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        if group is None:
            form.add_error(None, "Группа менеджеров пока не настроена.")
        else:
            try:
                with transaction.atomic():
                    employee = form.save()
                    employee.groups.add(group)
            except IntegrityError:
                if not User.objects.filter(username=form.cleaned_data["username"]).exists():
                    raise
                form.add_error("username", "Сотрудник с таким логином уже существует.")
            else:
                messages.success(request, f"Сотрудник «{employee.username}» добавлен.")
                return redirect("manager:employees")

    return render(request, "manager/employees.html", {"form": form, "employees": employees})
