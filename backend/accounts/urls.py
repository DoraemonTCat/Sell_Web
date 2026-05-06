# ===========================================
# Accounts URL Configuration
# /api/auth/ — Authentication endpoints
# ===========================================
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Google OAuth login — รับ token → return JWT
    path('google/', views.GoogleLoginView.as_view(), name='google-login'),

    # อัปเดต username + address หลัง login ครั้งแรก
    path('register/', views.RegisterView.as_view(), name='register'),

    # ดู/แก้ไข profile
    path('profile/', views.ProfileView.as_view(), name='profile'),

    # JWT token refresh — ใช้ refresh token ขอ access token ใหม่
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
