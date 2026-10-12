from rest_framework import permissions




def is_active_authenticated(user):
    return bool(
        user
        and user.is_authenticated
        and user.is_active
    )

def is_superuser(user):
    return bool(
        is_active_authenticated(user)
        and user.is_superuser
    )


def is_manager(user):
    return bool(
        is_active_authenticated(user)
        and (
            user.is_superuser
            or user.user_type == "MANAGER"
        )
    )

def can_manage_work(user):
    return bool(
        is_active_authentication(user)
        and (
            is_manager(user)
            or user.user_type == "DATA_ENTRY"
        )
    )

class IsSuperuserOrManager(permissions.BasePermission):
    def has_permission(self , request , view):
        return is_manager(request.user)
    
    def has_object_permission(self, request, view, obj):
        if not self.has_permission(request, view):
            return False

        if request.method in permissions.SAFE_METHODS:
                    return True

        if is_superuser(request.user):
            return True

        return not obj.is_superuser

class IsWorkAdministrator(permissions.BasePermission):

    def has_permission(self, request, view):
        return can_manage_work(request.user)


class IsDataEntryOrSuperUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False        
        if request.user.is_superuser:
            return True        
        if request.user.user_type == 'DATA_ENTRY':
            if request.method == 'DELETE':
                return False
            return True        
        return False