from rest_framework import permissions


def is_manager(user):
    """A manager is any staff or superuser account."""
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_manager(request.user)
