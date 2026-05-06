# ===========================================
# Order Views — Full Order Lifecycle
# create: ผู้ซื้อสร้าง order หลายสินค้า (ข้อ 1.5)
# upload_slip: ผู้ซื้ออัปโหลดสลิปชำระเงิน
# verify_payment: ผู้ขาย verify/reject สลิป (ข้อ 1.6)
# delivery_slip: ผู้ขายปริ้นใบส่งของ + ลด stock (ข้อ 1.7)
# ===========================================
import logging
from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from products.models import Product
from .models import SaleOrder, OrderItem, Payment, DeliverySlip
from .serializers import (
    CreateOrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
    PaymentSerializer,
    PaymentVerifySerializer,
    DeliverySlipSerializer,
)
from .permissions import IsBuyerOfOrder, IsSellerOfOrder
from .tasks import deduct_stock_task

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """
    Order API — คำสั่งซื้อ

    Buyer endpoints:
    POST   /api/orders/                  — สร้าง order (ข้อ 1.5)
    GET    /api/orders/my_orders/        — ดู order ของฉัน
    POST   /api/orders/{id}/upload_slip/ — อัปโหลดสลิปชำระเงิน

    Seller endpoints:
    GET    /api/orders/seller_orders/        — ดู order ที่มีสินค้าของฉัน
    POST   /api/orders/{id}/verify_payment/ — verify/reject สลิป (ข้อ 1.6)
    POST   /api/orders/{id}/delivery_slip/  — ปริ้นใบส่งของ + ลด stock (ข้อ 1.7)
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SaleOrder.objects.select_related('buyer').prefetch_related('items__product').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return CreateOrderSerializer
        return OrderDetailSerializer

    def create(self, request):
        """
        POST /api/orders/
        สร้าง order ใหม่ (ข้อ 1.5 — เลือกสินค้าหลายประเภทหลายชิ้น)
        Body: { "items": [{ "product_id": 1, "quantity": 2 }, ...] }
        """
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items_data = serializer.validated_data['items']

        with transaction.atomic():
            # ตรวจสอบ stock ทุก item ก่อนสร้าง
            order_items = []
            total = 0

            for item in items_data:
                product = Product.objects.select_for_update().get(id=item['product_id'])

                if not product.is_active:
                    return Response(
                        {'error': f'สินค้า "{product.title}" ไม่พร้อมจำหน่าย'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if product.quantity < item['quantity']:
                    return Response(
                        {'error': f'สินค้า "{product.title}" stock ไม่พอ (เหลือ {product.quantity})'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                subtotal = product.unit_price * item['quantity']
                order_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'unit_price': product.unit_price,
                    'subtotal': subtotal,
                })
                total += subtotal

            # สร้าง order
            order = SaleOrder.objects.create(
                buyer=request.user,
                total_amount=total,
            )

            # สร้าง order items
            for item in order_items:
                OrderItem.objects.create(order=order, **item)

        logger.info(f"Order created: {order.order_number} by {request.user.username}")

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    # --- Buyer Actions ---

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """GET /api/orders/my_orders/ — ดู order ของฉัน (buyer)."""
        orders = SaleOrder.objects.filter(buyer=request.user).order_by('-created_at')
        return Response(OrderListSerializer(orders, many=True).data)

    @action(detail=True, methods=['post'])
    def upload_slip(self, request, pk=None):
        """
        POST /api/orders/{id}/upload_slip/
        ผู้ซื้ออัปโหลดสลิปชำระเงิน
        """
        order = self.get_object()

        # ตรวจสิทธิ์: ต้องเป็นผู้ซื้อ
        if order.buyer != request.user:
            return Response({'error': 'ไม่ใช่ order ของคุณ'}, status=status.HTTP_403_FORBIDDEN)

        # ตรวจสถานะ: ต้องเป็น PENDING
        if order.status != 'PENDING':
            return Response({'error': 'สถานะ order ไม่ถูกต้อง'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        Payment.objects.create(
            order=order,
            paid_at=timezone.now(),
            **serializer.validated_data
        )

        # เปลี่ยนสถานะ order → PAID
        order.status = 'PAID'
        order.save(update_fields=['status', 'updated_at'])

        logger.info(f"Payment slip uploaded for {order.order_number} — status → PAID")
        return Response({'message': 'อัปโหลดสลิปสำเร็จ รอผู้ขายตรวจสอบ'})

    # --- Seller Actions ---

    @action(detail=False, methods=['get'])
    def seller_orders(self, request):
        """GET /api/orders/seller_orders/ — ดู order ที่มีสินค้าของฉัน (seller)."""
        orders = SaleOrder.objects.filter(
            items__product__seller=request.user
        ).distinct().order_by('-created_at')
        return Response(OrderListSerializer(orders, many=True).data)

    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """
        POST /api/orders/{id}/verify_payment/
        ผู้ขาย verify/reject สลิปชำระเงิน (ข้อ 1.6)
        Body: { "action": "VERIFIED", "note": "ตรวจสอบแล้ว" }
        """
        order = self.get_object()

        # ตรวจสิทธิ์: ต้องเป็นผู้ขายที่มีสินค้าใน order
        if not order.items.filter(product__seller=request.user).exists():
            return Response({'error': 'คุณไม่มีสินค้าใน order นี้'}, status=status.HTTP_403_FORBIDDEN)

        if not hasattr(order, 'payment'):
            return Response({'error': 'ยังไม่มีสลิปชำระเงิน'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PaymentVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = order.payment
        payment.status = serializer.validated_data['action']
        payment.note = serializer.validated_data.get('note', '')
        payment.save()

        # ถ้า REJECTED → กลับไป PENDING ให้ buyer ส่งสลิปใหม่
        if payment.status == 'REJECTED':
            order.status = 'PENDING'
            order.save(update_fields=['status', 'updated_at'])
            # ลบ payment เก่าเพื่อให้ส่งสลิปใหม่ได้
            payment.delete()

        logger.info(f"Payment {serializer.validated_data['action']} for {order.order_number}")
        return Response({'message': f'สลิป {serializer.validated_data["action"]}', 'order_status': order.status})

    @action(detail=True, methods=['post'])
    def delivery_slip(self, request, pk=None):
        """
        POST /api/orders/{id}/delivery_slip/
        ปริ้นใบส่งของ + ลด stock (ข้อ 1.7)
        Body: { "tracking_number": "TH12345678" } (optional)

        Rules:
        - Order ต้อง status = PAID (ต้อง verify payment ก่อน)
        - สร้าง DeliverySlip + เรียก Celery task ลด stock
        - อัปเดตสถานะเป็น SHIPPED
        """
        order = self.get_object()

        # ตรวจสิทธิ์
        if not order.items.filter(product__seller=request.user).exists():
            return Response({'error': 'คุณไม่มีสินค้าใน order นี้'}, status=status.HTTP_403_FORBIDDEN)

        # ตรวจสถานะ: ต้อง PAID
        if order.status != 'PAID':
            return Response(
                {'error': 'ต้อง verify payment ก่อนปริ้นใบส่งของ (สถานะปัจจุบัน: ' + order.status + ')'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ตรวจว่ายังไม่มีใบส่งของ
        if hasattr(order, 'delivery_slip'):
            return Response(
                DeliverySlipSerializer(order.delivery_slip).data,
                status=status.HTTP_200_OK
            )

        tracking = request.data.get('tracking_number', '')

        # สร้างใบส่งของ
        slip = DeliverySlip.objects.create(
            order=order,
            tracking_number=tracking,
            printed_at=timezone.now()
        )

        # อัปเดตสถานะ order
        order.status = 'SHIPPED'
        order.save(update_fields=['status'])

        # เรียก Celery task ลด stock (background)
        deduct_stock_task.delay(order.id)

        logger.info(f"Delivery slip created: {slip.slip_number} for {order.order_number}")

        return Response(
            DeliverySlipSerializer(slip).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def confirm_received(self, request, pk=None):
        """
        POST /api/orders/{id}/confirm_received/
        ผู้ซื้อยืนยันว่าได้รับสินค้าแล้ว (SHIPPED → COMPLETED)
        """
        order = self.get_object()

        # ตรวจสิทธิ์: ต้องเป็นผู้ซื้อ
        if order.buyer != request.user:
            return Response({'error': 'ไม่ใช่ order ของคุณ'}, status=status.HTTP_403_FORBIDDEN)

        # ตรวจสถานะ: ต้องเป็น SHIPPED
        if order.status != 'SHIPPED':
            return Response(
                {'error': f'สถานะ order ไม่ถูกต้อง (ปัจจุบัน: {order.status})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        order.status = 'COMPLETED'
        order.save(update_fields=['status', 'updated_at'])

        logger.info(f"Order {order.order_number} COMPLETED by {request.user.username}")
        return Response({'message': 'ยืนยันรับสินค้าสำเร็จ', 'order_status': 'COMPLETED'})
