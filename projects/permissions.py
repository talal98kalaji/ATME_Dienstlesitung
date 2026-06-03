from rest_framework import permissions




class IsSeniorFullStack(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'FULLSTACK_DEV' and 
            request.user.level == 'SENIOR'
        )


class IsProjectMember(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'employees'):
            return request.user in obj.employees.all()        
        if hasattr(obj, 'project'):
            return request.user in obj.project.employees.all()
        
        return False



class CanModifyTaskStatus(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.assigned_to == request.user:
            return True
        if (request.user.user_type == 'FULLSTACK_DEV' and 
            request.user.level == 'SENIOR' and 
            request.user in obj.project.employees.all()):
            return True            
        return False