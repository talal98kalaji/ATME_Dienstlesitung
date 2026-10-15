from django.urls import path

from . import views
from . import password_views


urlpatterns = [
    path(
        "login/",
        password_views.login_view,
        name="login",
    ),
    path(
        "password/change/",
        password_views.change_password,
        name="password-change",
    ),
    path(
        "password/reset/confirm/",
        password_views.confirm_reset,
        name="password-reset-confirm",
    ),
    path(
        "employees/<int:pk>/password-reset-token/",
        password_views.issue_reset_token,
        name="password-reset-token",
    ),
    path(
        "employees/",
        views.get_all_employees,
        name="get-all-employees",
    ),
    path(
        "employees/create/",
        views.create_employee,
        name="create-employee",
    ),
    path(
        "employees/<int:pk>/",
        views.get_employee_detail,
        name="get-employee-detail",
    ),
    path(
        "employees/<int:pk>/update/",
        views.update_employee,
        name="update-employee",
    ),
    path(
        "employees/<int:pk>/delete/",
        views.delete_employee,
        name="delete-employee",
    ),
]