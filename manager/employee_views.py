from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from accounts.models import User

from .forms import EmployeeCreationForm, EmployeeEmailForm
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
                if User.objects.filter(username=form.cleaned_data["username"]).exists():
                    form.add_error("username", "Сотрудник с таким логином уже существует.")
                elif User.objects.filter(email__iexact=form.cleaned_data["email"]).exists():
                    form.add_error("email", "Этот адрес уже используется.")
                else:
                    raise
            else:
                messages.success(request, f"Сотрудник «{employee.username}» добавлен.")
                return redirect("manager:employees")

    return render(request, "manager/employees.html", {"form": form, "employees": employees})


@never_cache
@login_required(login_url="manager:login")
@require_http_methods(["GET", "POST"])
def employee_email_view(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    eligible_users = User.objects.filter(Q(groups__name=MANAGERS_GROUP_NAME) | Q(pk=request.user.pk)).distinct()
    employee = get_object_or_404(eligible_users, pk=pk)
    form = EmployeeEmailForm(request.POST if request.method == "POST" else None, instance=employee)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save(commit=False).save(update_fields=["email"])
        except IntegrityError:
            if not User.objects.exclude(pk=pk).filter(email__iexact=form.cleaned_data["email"]).exists():
                raise
            form.add_error("email", "Этот адрес уже используется.")
        else:
            messages.success(request, f"Почта сотрудника «{employee.username}» сохранена.")
            return redirect("manager:employees")

    return render(request, "manager/employee_email.html", {"form": form, "employee": employee})
