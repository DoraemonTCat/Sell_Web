# ===========================================
# Order Permissions
# IsBuyerOfOrder: เฉพาะผู้ซื้อของ order นั้น
# IsSellerOfOrder: เฉพาะผู้ขายที่มีสินค้าใน order นั้น
# ===========================================
from rest_framework import permissions


class IsBuyerOfOrder(permissions.BasePermission):
    """
    อนุญาตเฉพาะผู้ซื้อของ order
    - Buyer ดูได้เฉพาะ order ของตัวเอง
    - Buyer ห้ามดู order คนอื่น
    """
    def has_object_permission(self, request, view, obj):
        return obj.buyer == request.user


class IsSellerOfOrder(permissions.BasePermission):
    """
    อนุญาตเฉพาะผู้ขายที่มีสินค้าใน order
    - Seller เห็นเฉพาะ order ที่มีสินค้าของตัวเอง
    - ใช้ตรวจสอบว่า seller เป็นเจ้าของสินค้าอย่างน้อย 1 ชิ้นใน order
    """
    def has_object_permission(self, request, view, obj):
        return obj.items.filter(product__seller=request.user).exists()
