from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS
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
                raise PermissionDenied("Sorry You cannot access admin's data")
           return True
        if obj.role == "ADMIN" and request.method in ['PUT', 'DELETE', 'PATCH']:
            raise PermissionDenied("Sorry you cannot delete or modify an admin user data")
        return True

class AdminReadOnlyForOthers(BasePermission):
    def has_permission(self, request, view):
        # This is the permission to check if the user is an admin
        if not request.user.is_authenticated or request.user.role != "ADMIN":
            raise PermissionDenied("Sorry you dont have permission to access this view")
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS and request.user.role != "ADMIN":
            raise PermissionDenied("Sorry you can not access the admin data information if you're not an admin")
        
         # Admins cannot update/delete other admins
        if obj.role == "ADMIN"  and request.method in ['PUT', 'PATCH', 'DELETE']:
            if obj != request.user:
                raise PermissionDenied({"error": "Sorry you dont have permission to modify or delete another admin data"})
        return True