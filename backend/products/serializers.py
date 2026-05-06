# ===========================================
# Product Serializers
# ProductListSerializer: แสดงรายการสินค้า (image, title, price) — ตามข้อ 2.3
# ProductDetailSerializer: แสดงรายละเอียดสินค้าทั้งหมด
# ProductCreateSerializer: สร้าง/แก้ไขสินค้า (สำหรับผู้ขาย)
# StockUpdateSerializer: เพิ่ม stock (สำหรับผู้ขาย)
# ===========================================
from rest_framework import serializers
from .models import Product, StockLog


class SellerInfoSerializer(serializers.Serializer):
    """ข้อมูลผู้ขายแบบย่อ (แสดงใน product card)."""
    id = serializers.IntegerField()
    username = serializers.CharField()


class ProductListSerializer(serializers.ModelSerializer):
    """
    Serializer สำหรับ Product List API (ข้อ 2.3)
    แสดงเฉพาะ: ภาพ, ชื่อสินค้า, ราคาต่อชิ้น, ข้อมูลผู้ขาย
    """
    seller = SellerInfoSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'image', 'title', 'unit_price', 'seller', 'created_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer สำหรับหน้ารายละเอียดสินค้า — แสดงทุก field."""
    seller = SellerInfoSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'seller', 'title', 'description',
            'unit_price', 'quantity', 'image',
            'is_active', 'created_at', 'updated_at'
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    """
    Serializer สำหรับสร้าง/แก้ไขสินค้า
    seller จะถูก set อัตโนมัติจาก request.user
    """
    class Meta:
        model = Product
        fields = ['title', 'description', 'unit_price', 'quantity', 'image']

    def validate_unit_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('ราคาต้องมากกว่า 0')
        return value


class StockUpdateSerializer(serializers.Serializer):
    """
    Serializer สำหรับเพิ่ม/ลด stock (ข้อ 1.3)
    quantity_change: จำนวนที่เพิ่ม (บวก) หรือลด (ลบ)
    """
    quantity_change = serializers.IntegerField(
        help_text="จำนวนที่เพิ่ม (+) หรือลด (-)"
    )
    reason = serializers.ChoiceField(
        choices=StockLog.REASON_CHOICES,
        default='RESTOCK'
    )
    note = serializers.CharField(required=False, default='')

    def validate_quantity_change(self, value):
        if value == 0:
            raise serializers.ValidationError('จำนวนต้องไม่เป็น 0')
        return value


class StockLogSerializer(serializers.ModelSerializer):
    """Serializer สำหรับดู log การเปลี่ยนแปลง stock."""
    class Meta:
        model = StockLog
        fields = ['id', 'quantity_change', 'reason', 'note', 'created_at']
