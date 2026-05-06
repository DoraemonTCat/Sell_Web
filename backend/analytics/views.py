# ===========================================
# Analytics Views — User Behavior Tracking
# track: บันทึก action ผู้ใช้ (VIEW, ADD_CART, PURCHASE)
# potential_customers: แสดง user ที่ add to cart แต่ไม่ซื้อ
# ===========================================
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Subquery
from .models import UserBehavior
from .serializers import TrackBehaviorSerializer, PotentialCustomerSerializer

logger = logging.getLogger(__name__)


class TrackBehaviorView(APIView):
    """
    POST /api/analytics/track/
    บันทึกพฤติกรรมผู้ใช้
    Body: { "product": 1, "action": "ADD_CART", "metadata": {"quantity": 2} }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TrackBehaviorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        logger.info(
            f"Behavior tracked: {request.user.username} "
            f"→ {serializer.validated_data['action']} "
            f"→ product {serializer.validated_data['product']}"
        )
        return Response({'message': 'บันทึกสำเร็จ'}, status=status.HTTP_201_CREATED)


class PotentialCustomersView(APIView):
    """
    GET /api/analytics/potential-customers/
    แสดง user ที่ add to cart แต่ยังไม่ซื้อสินค้าของ seller
    ใช้สำหรับ seller dashboard — ระบุลูกค้าที่สนใจแต่ยังไม่ตัดสินใจ
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        seller = request.user

        # หา product IDs ของ seller
        seller_product_ids = seller.products.values_list('id', flat=True)

        if not seller_product_ids:
            return Response([])

        # หา users ที่ ADD_CART สินค้าของ seller
        added_to_cart = UserBehavior.objects.filter(
            product_id__in=seller_product_ids,
            action='ADD_CART'
        )

        # หา users ที่ PURCHASE สินค้าของ seller
        purchased = UserBehavior.objects.filter(
            product_id__in=seller_product_ids,
            action='PURCHASE'
        ).values_list('user_id', 'product_id')

        # กรองเฉพาะ user ที่ add แต่ไม่ purchase
        purchased_set = set(purchased)
        potential = []

        for behavior in added_to_cart.select_related('user', 'product'):
            if (behavior.user_id, behavior.product_id) not in purchased_set:
                potential.append({
                    'user_id': behavior.user_id,
                    'username': behavior.user.username,
                    'email': behavior.user.email,
                    'product_id': behavior.product_id,
                    'product_title': behavior.product.title,
                    'added_at': behavior.created_at,
                })

        # ลบ duplicate (user+product ซ้ำ)
        seen = set()
        unique_potential = []
        for p in potential:
            key = (p['user_id'], p['product_id'])
            if key not in seen:
                seen.add(key)
                unique_potential.append(p)

        serializer = PotentialCustomerSerializer(unique_potential, many=True)
        return Response(serializer.data)
