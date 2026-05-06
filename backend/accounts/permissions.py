# ===========================================
# Accounts Permissions
# IsOwner: อนุญาตเฉพาะเจ้าของ resource
# ===========================================
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    อนุญาตเฉพาะเจ้าของ object เท่านั้น
    ใช้กับ views ที่ต้องการให้ user แก้ไขข้อมูลของตัวเองเท่านั้น
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user
