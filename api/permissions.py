from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

class IsAdminManagingUsers(BasePermission):
    """
    Custom permission:
    - Only admins can access the view.
    - Admins cannot update or delete fellow admins.
    """
    def has_permission(self, request, view):
        # Ensurre that only admin can access this view
        if not request.user.is_authenticated or request.user.role != "ADMIN":
            raise PermissionDenied("Access denied: you are not authorized to view this resource")
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
           if obj.role == "ADMIN" and obj.id != request.user.id:
                raise PermissionDenied("Sorry You cannot access another admin's data")
           return True
        if obj.role == "ADMIN" and request.method in ['PUT', 'DELETE', 'PATCH']:
            print(obj)
            print(request.user)
            raise PermissionDenied("Sorry you cannot delete or modify another admin user data")
        return True
    