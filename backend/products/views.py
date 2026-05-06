# ===========================================
# Product Views — CRUD + Stock Management
# ProductViewSet: สร้าง/ดู/แก้ไข/ลบ สินค้า + search/filter/sort
# stock action: เพิ่ม stock สินค้า (ข้อ 1.3)
# ===========================================
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db import transaction
from .models import Product, StockLog
from .serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    StockUpdateSerializer,
    StockLogSerializer,
)
from .filters import ProductFilter
from .permissions import IsProductOwner

logger = logging.getLogger(__name__)


class ProductViewSet(viewsets.ModelViewSet):
    """
    Product API — สินค้าทั้งหมดในระบบ

    GET /api/products/          — ดูรายการสินค้า (public, ข้อ 1.4)
    GET /api/products/{id}/     — ดูรายละเอียดสินค้า
    POST /api/products/         — สร้างสินค้าใหม่ (seller only, ข้อ 1.2)
    PATCH /api/products/{id}/   — แก้ไขสินค้า (owner only)
    DELETE /api/products/{id}/  — ลบสินค้า (owner only)

    Query params:
    - ?search=keyword       ค้นหาจากชื่อ/รายละเอียด
    - ?min_price=100        ราคาขั้นต่ำ
    - ?max_price=5000       ราคาสูงสุด
    - ?seller=3             กรองตามผู้ขาย
    - ?ordering=-unit_price เรียงตามราคา (- = มากไปน้อย)
    """
    permission_classes = [IsAuthenticatedOrReadOnly, IsProductOwner]
    filterset_class = ProductFilter
    search_fields = ['title', 'description']
    ordering_fields = ['unit_price', 'created_at', 'title']
    ordering = ['-created_at']  # เรียงใหม่สุดก่อน

    def get_queryset(self):
        """แสดงเฉพาะสินค้าที่ is_active=True (สำหรับ public)."""
        qs = Product.objects.select_related('seller').all()
        # ถ้าไม่ใช่เจ้าของ → แสดงเฉพาะ active
        if not self.request.user.is_authenticated:
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        """ใช้ serializer ที่ต่างกันตาม action."""
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        return ProductDetailSerializer

    def perform_create(self, serializer):
        """ตั้ง seller เป็น user ที่กำลัง login อยู่."""
        product = serializer.save(seller=self.request.user)
        # บันทึก stock log สำหรับ initial quantity
        if product.quantity > 0:
            StockLog.objects.create(
                product=product,
                quantity_change=product.quantity,
                reason='RESTOCK',
                note='จำนวนเริ่มต้นตอนสร้างสินค้า'
            )
        logger.info(f"Product created: {product.title} by {self.request.user.username}")

    # --- Custom Actions ---

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsProductOwner])
    def stock(self, request, pk=None):
        """
        POST /api/products/{id}/stock/
        เพิ่มสินค้าในคลัง (ข้อ 1.3)
        Body: { "quantity_change": 50, "reason": "RESTOCK", "note": "เติม stock รอบ 2" }
        """
        product = self.get_object()
        serializer = StockUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        qty = serializer.validated_data['quantity_change']
        reason = serializer.validated_data['reason']
        note = serializer.validated_data.get('note', '')

        # ตรวจสอบว่า stock ไม่ติดลบ
        new_qty = product.quantity + qty
        if new_qty < 0:
            return Response(
                {'error': f'Stock ไม่เพียงพอ (ปัจจุบัน: {product.quantity})'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atomic update เพื่อป้องกัน race condition
        with transaction.atomic():
            product.quantity = new_qty
            product.save(update_fields=['quantity'])
            StockLog.objects.create(
                product=product,
                quantity_change=qty,
                reason=reason,
                note=note
            )

        logger.info(f"Stock updated: {product.title} {'+' if qty > 0 else ''}{qty} → {new_qty}")

        return Response({
            'product_id': product.id,
            'title': product.title,
            'previous_quantity': product.quantity - qty,
            'change': qty,
            'new_quantity': new_qty,
        })

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsProductOwner])
    def stock_logs(self, request, pk=None):
        """
        GET /api/products/{id}/stock_logs/
        ดู log การเปลี่ยนแปลง stock ทั้งหมด
        """
        product = self.get_object()
        logs = product.stock_logs.all()[:50]
        return Response(StockLogSerializer(logs, many=True).data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def my_products(self, request):
        """
        GET /api/products/my_products/
        ดูสินค้าของตัวเอง (สำหรับ seller dashboard)
        """
        products = Product.objects.filter(seller=request.user)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
