# ===========================================
# Analytics URL Configuration
# ===========================================
from django.urls import path
from . import views

urlpatterns = [
    # บันทึกพฤติกรรมผู้ใช้
    path('track/', views.TrackBehaviorView.as_view(), name='track-behavior'),

    # AI แนะนำสินค้า (cosine similarity)
    path('recommendations/', views.RecommendationView.as_view(), name='recommendations'),

    # ดู potential customers (seller dashboard)
    path('potential-customers/', views.PotentialCustomersView.as_view(), name='potential-customers'),

    # สถิติร้านค้า (seller dashboard)
    path('seller-stats/', views.SellerStatsView.as_view(), name='seller-stats'),
]
