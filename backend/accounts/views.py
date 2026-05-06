# ===========================================
# Accounts Views — Authentication & Profile
# GoogleLoginView: รับ Google token → สร้าง/ดึง User → return JWT
# RegisterView: อัปเดต username + address หลัง login ครั้งแรก
# ProfileView: ดู/แก้ไข profile ของตัวเอง
# ===========================================
import logging
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from .serializers import GoogleAuthSerializer, RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class GoogleLoginView(APIView):
    """
    POST /api/auth/google/
    รับ Google ID token → verify → สร้าง/ดึง User → return JWT tokens

    Flow:
    1. Frontend ทำ Google OAuth → ได้ ID token
    2. ส่ง token มาที่ endpoint นี้
    3. Backend verify token กับ Google API
    4. สร้าง User ใหม่ (ถ้ายังไม่มี) หรือดึง User เดิม
    5. Return JWT access + refresh tokens
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        google_data = serializer.validated_data['token']

        # ดึงข้อมูลจาก Google token
        google_id = google_data['sub']
        email = google_data.get('email', '')
        name = google_data.get('name', '')
        avatar = google_data.get('picture', '')

        # สร้าง/ดึง User
        user, created = User.objects.get_or_create(
            google_id=google_id,
            defaults={
                'email': email,
                'username': email.split('@')[0],  # ใช้ส่วนหน้า @ เป็น username ชั่วคราว
                'avatar_url': avatar,
            }
        )

        # อัปเดต avatar ทุกครั้งที่ login (อาจเปลี่ยน)
        if not created:
            user.avatar_url = avatar
            user.save(update_fields=['avatar_url'])

        # สร้าง JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f"User {'created' if created else 'logged in'}: {email}")

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
            'is_new_user': created,  # Frontend ใช้เพื่อ redirect ไปหน้า register
        }, status=status.HTTP_200_OK)


class RegisterView(generics.UpdateAPIView):
    """
    PATCH /api/auth/register/
    อัปเดต username + address หลัง Google login ครั้งแรก
    ผู้ใช้ต้องกรอกข้อมูลก่อนใช้งานระบบได้
    """

    serializer_class = RegisterSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # คืน UserSerializer แทน RegisterSerializer เพื่อให้มี id
        return Response(UserSerializer(instance).data)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET /api/auth/profile/ — ดู profile ตัวเอง
    PATCH /api/auth/profile/ — แก้ไข username, address
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
