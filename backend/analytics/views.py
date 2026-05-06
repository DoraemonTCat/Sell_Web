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


class RecommendationView(APIView):
    """
    GET /api/analytics/recommendations/
    แนะนำสินค้าด้วย AI (Cosine Similarity)
    - ถ้า user login → collaborative filtering จาก behavior
    - ถ้าไม่ login → สินค้ายอดนิยม / ล่าสุด
    """
    permission_classes = []  # Public — ไม่ต้อง login

    def get(self, request):
        from .recommendations import get_recommendations, get_popular_products
        from products.serializers import ProductListSerializer

        if request.user.is_authenticated:
            products = get_recommendations(request.user.id, limit=8)
        else:
            products = get_popular_products(limit=8)

        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class SellerStatsView(APIView):
    """
    GET /api/analytics/seller-stats/
    สถิติร้านค้าสำหรับ seller dashboard
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from products.models import Product
        from orders.models import SaleOrder, OrderItem
        from django.db.models import Sum, Count

        seller = request.user

        # จำนวนสินค้า
        product_count = Product.objects.filter(seller=seller).count()

        # จำนวน order ที่มีสินค้าของ seller
        order_ids = OrderItem.objects.filter(
            product__seller=seller
        ).values_list('order_id', flat=True).distinct()

        total_orders = len(set(order_ids))

        # ยอดขายรวม (เฉพาะ order COMPLETED)
        completed_revenue = OrderItem.objects.filter(
            product__seller=seller,
            order__status='COMPLETED'
        ).aggregate(total=Sum('subtotal'))['total'] or 0

        # จำนวน potential customers
        seller_product_ids = Product.objects.filter(seller=seller).values_list('id', flat=True)
        potential_count = UserBehavior.objects.filter(
            product_id__in=seller_product_ids,
            action='ADD_CART'
        ).exclude(
            user_id__in=UserBehavior.objects.filter(
                product_id__in=seller_product_ids,
                action='PURCHASE'
            ).values_list('user_id', flat=True)
        ).values('user_id').distinct().count()

        return Response({
            'product_count': product_count,
            'total_orders': total_orders,
            'completed_revenue': float(completed_revenue),
            'potential_customers': potential_count,
        })
