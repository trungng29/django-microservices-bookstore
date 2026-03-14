from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import LoginAttempt, SellerProfile, AuthorProfile, UserRole, Role
from .serializers import (
    RegisterSerializer, CustomTokenObtainPairSerializer,
    UserProfileSerializer, UpdateProfileSerializer, ChangePasswordSerializer,
    SellerProfileSerializer, AuthorProfileSerializer,
)
from .utils import custom_exception_handler  # noqa

User = get_user_model()


def get_client_ip(request):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    return x.split(',')[0] if x else request.META.get('REMOTE_ADDR')


class AuthRateThrottle(AnonRateThrottle):
    rate = '10/minute'
    scope = 'auth'


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Body: { email, username, password, password2, role?, first_name?, last_name? }
    role: customer (default) | seller | author
    """
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        refresh['roles']        = user.roles
        refresh['primary_role'] = user.primary_role
        refresh['permissions']  = user.get_all_permissions_flat()
        refresh['username']     = user.username
        refresh['email']        = user.email
        refresh['is_verified']  = user.is_verified

        return Response({
            "message": "Tạo tài khoản thành công.",
            "user":    UserProfileSerializer(user, context={'request': request}).data,
            "tokens": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Body: { email, password }
    Response: { access, refresh, user: { roles, permissions, ... } }
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        ip    = get_client_ip(request)
        email = request.data.get('email', '')
        resp  = super().post(request, *args, **kwargs)

        LoginAttempt.objects.create(
            email=email, ip_address=ip,
            success=(resp.status_code == 200),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        return resp


# ── Logout ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """POST /api/auth/logout/  Body: { refresh }"""
    try:
        token = RefreshToken(request.data.get('refresh'))
        token.blacklist()
        return Response({"message": "Đăng xuất thành công."})
    except TokenError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/auth/profile/"""
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        return UpdateProfileSerializer if self.request.method in ('PUT', 'PATCH') else UserProfileSerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        return Response(UserProfileSerializer(request.user, context={'request': request}).data)

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# ── Change Password ───────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """POST /api/auth/change-password/"""
    s = ChangePasswordSerializer(data=request.data, context={'request': request})
    s.is_valid(raise_exception=True)
    request.user.set_password(s.validated_data['new_password'])
    request.user.save()
    refresh = RefreshToken.for_user(request.user)
    return Response({
        "message": "Đổi mật khẩu thành công.",
        "tokens":  {"access": str(refresh.access_token), "refresh": str(refresh)},
    })


# ── Role management (admin only) ──────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def assign_role(request):
    """
    POST /api/auth/roles/assign/
    Body: { user_id, role }   — admin only
    """
    if not request.user.has_role('admin'):
        return Response({"error": "Không có quyền thực hiện."}, status=status.HTTP_403_FORBIDDEN)

    user_id   = request.data.get('user_id')
    role_name = request.data.get('role')

    if role_name not in ['customer', 'seller', 'author', 'admin']:
        return Response({"error": "Role không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "User không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

    target.assign_role(role_name)
    return Response({
        "message": f"Đã gán role '{role_name}' cho {target.username}.",
        "roles":   target.roles,
    })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def revoke_role(request):
    """
    POST /api/auth/roles/revoke/
    Body: { user_id, role }   — admin only
    """
    if not request.user.has_role('admin'):
        return Response({"error": "Không có quyền thực hiện."}, status=status.HTTP_403_FORBIDDEN)

    user_id   = request.data.get('user_id')
    role_name = request.data.get('role')

    try:
        target = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "User không tồn tại."}, status=status.HTTP_404_NOT_FOUND)

    target.remove_role(role_name)
    return Response({
        "message": f"Đã thu hồi role '{role_name}' của {target.username}.",
        "roles":   target.roles,
    })


# ── Seller Profile ────────────────────────────────────────────────────────────

class SellerProfileView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/auth/seller-profile/"""
    serializer_class   = SellerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not self.request.user.has_role('seller'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Chỉ Seller mới có profile này.")
        profile, _ = SellerProfile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# ── Author Profile ────────────────────────────────────────────────────────────

class AuthorProfileView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/auth/author-profile/"""
    serializer_class   = AuthorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        if not self.request.user.has_role('author'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Chỉ Author mới có profile này.")
        profile, _ = AuthorProfile.objects.get_or_create(user=self.request.user)
        return profile

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# ── Token Verify (dùng cho service-to-service) ────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verify_token(request):
    """
    GET /api/auth/verify/
    Các microservice khác gọi endpoint này để validate token
    và nhận đầy đủ thông tin user + roles + permissions.
    """
    user = request.user
    return Response({
        "valid": True,
        "user": {
            "id":           user.id,
            "email":        user.email,
            "username":     user.username,
            "roles":        user.roles,
            "primary_role": user.primary_role,
            "permissions":  user.get_all_permissions_flat(),
            "is_verified":  user.is_verified,
            "is_staff":     user.is_staff,
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    return Response({"status": "ok", "service": "auth_service"})
