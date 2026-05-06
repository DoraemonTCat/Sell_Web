# ===========================================
# Analytics URL Configuration
# ===========================================
from django.urls import path
from . import views

urlpatterns = [
    # บันทึกพฤติกรรมผู้ใช้
    path('track/', views.TrackBehaviorView.as_view(), name='track-behavior'),

    # ดู potential customers (seller dashboard)
    path('potential-customers/', views.PotentialCustomersView.as_view(), name='potential-customers'),
]
