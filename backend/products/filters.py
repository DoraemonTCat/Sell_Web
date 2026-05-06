# ===========================================
# Product Filters — django-filter
# ค้นหา: title
# กรอง: ช่วงราคา (min_price, max_price), seller
# เรียง: price, latest
# ===========================================
import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    """
    Filter สำหรับ Product List API
    - search: ค้นหาจากชื่อสินค้า
    - min_price / max_price: กรองช่วงราคา
    - seller: กรองตาม seller ID
    """
    min_price = django_filters.NumberFilter(
        field_name='unit_price',
        lookup_expr='gte',
        label='ราคาขั้นต่ำ'
    )
    max_price = django_filters.NumberFilter(
        field_name='unit_price',
        lookup_expr='lte',
        label='ราคาสูงสุด'
    )
    seller = django_filters.NumberFilter(
        field_name='seller__id',
        label='ID ผู้ขาย'
    )

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'seller']
