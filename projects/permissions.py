from rest_framework import permissions

from accounts.permissions import (
    can_manage_work,
    is_active_authenticated,
)


def is_senior_fullstack(user):
    return bool(
        is_active_authenticated(user)
        and user.user_type == 'FULLSTACK_DEV'
        and user.level == 'SENIOR'
    )


def can_manage_projects(user):
    return bool(
        can_manage_work(user)
        or is_senior_fullstack(user)
    )


class IsSeniorFullStack(permissions.BasePermission):

    def has_permission(self, request, view):
        return is_senior_fullstack(request.user)


class IsProjectAdministrator(permissions.BasePermission):

    def has_permission(self, request, view):
        return can_manage_projects(request.user)


class IsProjectMember(permissions.BasePermission):

    def has_permission(self, request, view):
        return is_active_authenticated(request.user)

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not is_active_authenticated(user):
            return False
        if can_manage_projects(user):
            return True
        if hasattr(obj, 'employees'):
            return obj.employees.filter(pk=user.pk).exists()
        if hasattr(obj, 'project'):
            return obj.project.employees.filter(
                pk=user.pk
            ).exists()

        return False


class CanModifyTaskStatus(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user

        if not is_active_authenticated(user):
            return False

        if can_manage_projects(user):
            return True

        return obj.assigned_to_id == user.pk