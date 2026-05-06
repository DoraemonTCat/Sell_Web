# ===========================================
# Analytics Serializers
# TrackBehaviorSerializer: บันทึกพฤติกรรมผู้ใช้
# PotentialCustomerSerializer: แสดงผู้ใช้ที่ add to cart แต่ไม่ซื้อ
# ===========================================
from rest_framework import serializers
from .models import UserBehavior


class TrackBehaviorSerializer(serializers.ModelSerializer):
    """บันทึกพฤติกรรมผู้ใช้ (VIEW, ADD_CART, REMOVE_CART, PURCHASE)."""
    class Meta:
        model = UserBehavior
        fields = ['product', 'action', 'metadata']


class UserBehaviorSerializer(serializers.ModelSerializer):
    """แสดง behavior log."""
    product_title = serializers.CharField(source='product.title', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = UserBehavior
        fields = ['id', 'username', 'product', 'product_title', 'action', 'metadata', 'created_at']


class PotentialCustomerSerializer(serializers.Serializer):
    """
    แสดง potential customer — user ที่ add to cart แต่ยังไม่ซื้อ
    """
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    product_id = serializers.IntegerField()
    product_title = serializers.CharField()
    added_at = serializers.DateTimeField()
