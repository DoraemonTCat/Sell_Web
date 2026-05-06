# ===========================================
# AI Recommendation Engine — Cosine Similarity
# แนะนำสินค้าโดยวิเคราะห์พฤติกรรมผู้ใช้:
# 1. สร้าง user-product matrix จาก UserBehavior
# 2. คำนวณ cosine similarity ระหว่าง users
# 3. แนะนำสินค้าที่ users คล้ายกันสนใจ
# ===========================================
import logging
from collections import defaultdict
from math import sqrt
from django.db.models import Count
from analytics.models import UserBehavior
from products.models import Product

logger = logging.getLogger(__name__)

# น้ำหนักแต่ละ action
ACTION_WEIGHTS = {
    'VIEW': 1,
    'ADD_CART': 3,
    'PURCHASE': 5,
    'REMOVE_CART': -1,
}


def get_user_product_matrix():
    """สร้าง user-product interaction matrix จาก UserBehavior."""
    behaviors = UserBehavior.objects.values('user_id', 'product_id', 'action')

    matrix = defaultdict(lambda: defaultdict(float))
    for b in behaviors:
        weight = ACTION_WEIGHTS.get(b['action'], 0)
        matrix[b['user_id']][b['product_id']] += weight

    return matrix


def cosine_similarity(vec_a, vec_b):
    """คำนวณ cosine similarity ระหว่าง 2 vectors."""
    # หา product IDs ที่ทั้ง 2 users มีร่วมกัน
    common_products = set(vec_a.keys()) & set(vec_b.keys())

    if not common_products:
        return 0.0

    # Dot product
    dot = sum(vec_a[p] * vec_b[p] for p in common_products)

    # Magnitudes
    mag_a = sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def get_recommendations(user_id, limit=8):
    """
    แนะนำสินค้าให้ user โดยใช้ collaborative filtering.

    Algorithm:
    1. สร้าง user-product matrix
    2. หา users ที่คล้าย target user (cosine similarity > 0)
    3. รวบรวมสินค้าที่ similar users สนใจ (แต่ target user ยังไม่เคยดู)
    4. จัดอันดับตาม weighted similarity score
    """
    matrix = get_user_product_matrix()

    # ถ้า user ยังไม่มี behavior → แนะนำสินค้ายอดนิยม
    if user_id not in matrix:
        return get_popular_products(limit)

    target_vec = matrix[user_id]
    target_products = set(target_vec.keys())

    # คำนวณ similarity กับ users อื่น
    similarities = []
    for other_user_id, other_vec in matrix.items():
        if other_user_id == user_id:
            continue
        sim = cosine_similarity(target_vec, other_vec)
        if sim > 0:
            similarities.append((other_user_id, sim))

    # เรียงตาม similarity สูงสุด
    similarities.sort(key=lambda x: x[1], reverse=True)

    # รวบรวมสินค้าจาก similar users
    product_scores = defaultdict(float)
    for other_user_id, sim in similarities[:20]:  # Top 20 similar users
        for product_id, score in matrix[other_user_id].items():
            if product_id not in target_products:
                product_scores[product_id] += score * sim

    # เรียงตาม score สูงสุด
    recommended_ids = sorted(product_scores, key=product_scores.get, reverse=True)[:limit]

    if not recommended_ids:
        return get_popular_products(limit)

    # ดึง Product objects
    products = Product.objects.filter(id__in=recommended_ids, quantity__gt=0)

    # เรียงตาม score
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in recommended_ids if pid in product_map]


def get_popular_products(limit=8):
    """
    Fallback: แนะนำสินค้ายอดนิยม (จำนวน VIEW + PURCHASE มากสุด).
    ใช้เมื่อ user ใหม่ยังไม่มี behavior data.
    """
    popular_ids = (
        UserBehavior.objects
        .filter(action__in=['VIEW', 'PURCHASE'])
        .values('product_id')
        .annotate(count=Count('id'))
        .order_by('-count')[:limit]
    )

    product_ids = [item['product_id'] for item in popular_ids]

    if not product_ids:
        # ถ้าไม่มี behavior data เลย → แนะนำสินค้าล่าสุด
        return list(Product.objects.filter(quantity__gt=0).order_by('-created_at')[:limit])

    products = Product.objects.filter(id__in=product_ids, quantity__gt=0)
    product_map = {p.id: p for p in products}
    return [product_map[pid] for pid in product_ids if pid in product_map]
