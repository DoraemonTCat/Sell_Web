# ===========================================
# Accounts Serializers
# GoogleAuthSerializer: รับ Google ID token → verify → return JWT
# RegisterSerializer: อัปเดต username + address หลัง login ครั้งแรก
# UserSerializer: ดู/แก้ไข profile
# ===========================================
from rest_framework import serializers
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User


class GoogleAuthSerializer(serializers.Serializer):
    """
    รับ Google ID token จาก frontend
    → verify กับ Google API
    → สร้าง/ดึง User
    """
    token = serializers.CharField(
        required=True,
        help_text="Google ID token จาก frontend OAuth flow"
    )

    def validate_token(self, value):
        """Verify Google ID token และดึงข้อมูล user."""
        try:
            # Verify token กับ Google API
            idinfo = id_token.verify_oauth2_token(
                value,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # ตรวจสอบว่า token ออกโดย Google
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Invalid token issuer')

            return idinfo

        except ValueError:
            raise serializers.ValidationError('Invalid Google token')


class RegisterSerializer(serializers.ModelSerializer):
    """
    อัปเดต username + address หลัง Google login ครั้งแรก
    ผู้ใช้ต้องกรอกข้อมูลเพิ่มเติมก่อนใช้งานระบบ
    """
    class Meta:
        model = User
        fields = ['username', 'address', 'role']

    def validate_username(self, value):
        """ตรวจสอบ username ซ้ำ (ไม่นับ user ปัจจุบัน)."""
        user = self.context.get('request').user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError('Username นี้ถูกใช้แล้ว')
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializer สำหรับดู/แก้ไข profile."""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'address', 'role',
            'avatar_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'avatar_url', 'created_at', 'updated_at']
