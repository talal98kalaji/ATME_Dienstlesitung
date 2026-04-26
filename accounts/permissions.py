from rest_framework import permissions

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