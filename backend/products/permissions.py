# ===========================================
# Product Permissions
# IsProductOwner: เฉพาะ seller ที่เป็นเจ้าของสินค้าจึงแก้ไข/ลบได้
# ===========================================
from rest_framework import permissions


class IsProductOwner(permissions.BasePermission):
    """
    อนุญาตเฉพาะ seller ที่เป็นเจ้าของสินค้า
    - GET: ทุกคนดูได้ (public)
    - POST/PUT/PATCH/DELETE: เฉพาะเจ้าของ
    """
    def has_object_permission(self, request, view, obj):
        # อ่านได้ทุกคน
        if request.method in permissions.SAFE_METHODS:
            return True
        # แก้ไข/ลบ เฉพาะเจ้าของ
        return obj.seller == request.user
