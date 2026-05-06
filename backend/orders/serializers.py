# ===========================================
# Order Serializers
# OrderItemSerializer: แต่ละรายการสินค้าใน order
# CreateOrderSerializer: สร้าง order ใหม่ (หลายสินค้า, ข้อ 1.5)
# OrderListSerializer: แสดง order list
# OrderDetailSerializer: แสดงรายละเอียด order + items + payment + slip
# PaymentSerializer: บันทึก/อัปโหลดสลิปการชำระเงิน
# PaymentVerifySerializer: ผู้ขาย verify/reject payment
# DeliverySlipSerializer: ใบส่งของ
# ===========================================
from rest_framework import serializers
from .models import SaleOrder, OrderItem, Payment, DeliverySlip
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """แสดงรายการสินค้าใน order พร้อมข้อมูลสินค้า."""
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_title', 'product_image',
            'quantity', 'unit_price', 'subtotal'
        ]
        read_only_fields = ['unit_price', 'subtotal']


class OrderItemCreateSerializer(serializers.Serializer):
    """Input สำหรับสร้าง order item (product_id + quantity)."""
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class CreateOrderSerializer(serializers.Serializer):
    """
    สร้าง order ใหม่ (ข้อ 1.5)
    รับ list ของสินค้า + จำนวน → สร้าง SaleOrder + OrderItems
    ตรวจสอบ stock ว่าเพียงพอก่อนสร้าง
    """
    items = OrderItemCreateSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('ต้องมีสินค้าอย่างน้อย 1 รายการ')
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """อัปโหลดสลิปการชำระเงิน (ข้อ 1.6 — ฝั่ง buyer)."""
    class Meta:
        model = Payment
        fields = [
            'id', 'amount_received', 'payment_slip',
            'payment_method', 'status', 'note',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'note', 'paid_at', 'created_at']


class PaymentVerifySerializer(serializers.Serializer):
    """ผู้ขาย verify/reject payment slip (ข้อ 1.6 — ฝั่ง seller)."""
    action = serializers.ChoiceField(choices=['VERIFIED', 'REJECTED'])
    note = serializers.CharField(required=False, default='')


class DeliverySlipSerializer(serializers.ModelSerializer):
    """ใบส่งของ (ข้อ 1.7)."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    buyer_name = serializers.CharField(source='order.buyer.username', read_only=True)
    buyer_address = serializers.CharField(source='order.buyer.address', read_only=True)
    items = serializers.SerializerMethodField()

    class Meta:
        model = DeliverySlip
        fields = [
            'id', 'slip_number', 'order_number',
            'buyer_name', 'buyer_address',
            'tracking_number', 'stock_deducted',
            'printed_at', 'created_at', 'items'
        ]
        read_only_fields = ['slip_number', 'stock_deducted', 'printed_at']

    def get_items(self, obj):
        """แสดงรายการสินค้าใน order."""
        return OrderItemSerializer(obj.order.items.all(), many=True).data


class OrderListSerializer(serializers.ModelSerializer):
    """แสดง order list แบบย่อ."""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    item_count = serializers.SerializerMethodField()
    has_payment = serializers.SerializerMethodField()
    payment_slip_url = serializers.SerializerMethodField()

    class Meta:
        model = SaleOrder
        fields = [
            'id', 'order_number', 'buyer_name',
            'total_amount', 'status', 'item_count',
            'has_payment', 'payment_slip_url', 'created_at'
        ]

    def get_item_count(self, obj):
        return obj.items.count()

    def get_has_payment(self, obj):
        return hasattr(obj, 'payment')

    def get_payment_slip_url(self, obj):
        if hasattr(obj, 'payment') and obj.payment.payment_slip:
            return obj.payment.payment_slip.url
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """แสดงรายละเอียด order ครบ — items + payment + delivery slip."""
    buyer_name = serializers.CharField(source='buyer.username', read_only=True)
    buyer_address = serializers.CharField(source='buyer.address', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    delivery_slip = DeliverySlipSerializer(read_only=True)

    class Meta:
        model = SaleOrder
        fields = [
            'id', 'order_number', 'buyer', 'buyer_name', 'buyer_address',
            'total_amount', 'status',
            'items', 'payment', 'delivery_slip',
            'created_at', 'updated_at'
        ]
