from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST

from accounts.models import User

from .forms import EmployeeCreationForm, EmployeeDetailsForm, EmployeeEmailForm
from .signals import MANAGERS_GROUP_NAME


def employee_accounts():
    return User.objects.filter(groups__name=MANAGERS_GROUP_NAME, is_superuser=False)


def editable_accounts(owner_pk):
    return User.objects.filter(
        Q(groups__name=MANAGERS_GROUP_NAME, is_superuser=False) | Q(pk=owner_pk),
    ).distinct()


def add_employee_conflict_error(form):
    other_users = User.objects.exclude(pk=form.instance.pk)
    username = form.cleaned_data.get("username")
    if username and other_users.filter(username__iexact=username).exists():
        form.add_error("username", "Сотрудник с таким логином уже существует.")
    elif other_users.filter(email__iexact=form.cleaned_data["email"]).exists():
        form.add_error("email", "Этот адрес уже используется.")
    else:
        return False
    return True


@sensitive_post_parameters("password1", "password2")
@never_cache
@login_required(login_url="manager:login")
@require_http_methods(["GET", "POST"])
def employees_view(request):
    if not request.user.is_superuser:
        raise PermissionDenied

    group = Group.objects.filter(name=MANAGERS_GROUP_NAME).first()
    employees = employee_accounts().order_by("username")
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
                if not add_employee_conflict_error(form):
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

    employee = get_object_or_404(editable_accounts(request.user.pk), pk=pk)
    form = EmployeeEmailForm(request.POST if request.method == "POST" else None, instance=employee)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save(commit=False).save(update_fields=["email"])
        except IntegrityError:
            if not add_employee_conflict_error(form):
                raise
        else:
            messages.success(request, f"Почта сотрудника «{employee.username}» сохранена.")
            return redirect("manager:employees")

    return render(request, "manager/employee_email.html", {"form": form, "employee": employee})


@never_cache
@login_required(login_url="manager:login")
@require_http_methods(["GET", "POST"])
def employee_edit_view(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    employee = get_object_or_404(editable_accounts(request.user.pk), pk=pk)
    is_own_profile = employee.pk == request.user.pk
    form = EmployeeDetailsForm(request.POST if request.method == "POST" else None, instance=employee)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save(commit=False).save(update_fields=form.changed_data)
        except IntegrityError:
            if not add_employee_conflict_error(form):
                raise
        else:
            if is_own_profile:
                messages.success(request, "Профиль сохранён.")
            else:
                messages.success(request, f"Данные сотрудника «{employee.username}» сохранены.")
            return redirect("manager:employees")

    return render(request, "manager/employee_edit.html", {
        "form": form,
        "employee": employee,
        "is_own_profile": is_own_profile,
        "page_title": "Мой профиль" if is_own_profile else "Редактировать сотрудника",
    })


@never_cache
@login_required(login_url="manager:login")
@require_POST
def employee_access_view(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied

    employees = employee_accounts().filter(pk=pk)
    employee = get_object_or_404(employees)
    action = request.POST.get("action")
    if action == "disable":
        employees.filter(is_active=True).update(is_active=False, session_version=F("session_version") + 1)
        messages.success(request, f"Доступ сотрудника «{employee.username}» отключён.")
    elif action == "enable":
        employees.filter(is_active=False).update(is_active=True)
        messages.success(request, f"Доступ сотрудника «{employee.username}» включён.")
    else:
        return HttpResponseBadRequest()

    return redirect("manager:employee_edit", pk=pk)
