from rest_framework.permissions import BasePermission


class IsOrganizer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.role in ["organizer", "admin"]
        )


class IsEventOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (obj.organizer == user or user.role == "admin")
        )
