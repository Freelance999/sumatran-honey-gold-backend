from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsSuperUser(permissions.BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_superuser):
            raise PermissionDenied(detail=self.message)
        return True