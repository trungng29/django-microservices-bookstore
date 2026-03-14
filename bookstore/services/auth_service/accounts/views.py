from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import LoginAttempt
from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
    ChangePasswordSerializer,
)

User = get_user_model()


def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')


# ─── Throttle for auth endpoints ─────────────────────────────────────────────

class AuthRateThrottle(AnonRateThrottle):
    rate = '5/minute'
    scope = 'auth'


# ─── Register ────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Creates a new user. Password is hashed via Django's PBKDF2+SHA256.
    ID is auto-incremented BigInt.
    """
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes   = [AuthRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Issue tokens immediately on register
        refresh = RefreshToken.for_user(user)
        refresh['username']    = user.username
        refresh['email']       = user.email
        refresh['is_verified'] = user.is_verified

        return Response({
            "message": "Account created successfully.",
            "user": UserProfileSerializer(user, context={'request': request}).data,
            "tokens": {
                "access":  str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/
    Returns JWT access + refresh tokens with enriched user payload.
    Logs attempt for security audit.
    """
    serializer_class = CustomTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]

    def post(self, request, *args, **kwargs):
        ip = get_client_ip(request)
        email = request.data.get('email', '')

        response = super().post(request, *args, **kwargs)

        success = response.status_code == 200
        LoginAttempt.objects.create(
            email=email,
            ip_address=ip,
            success=success,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        if success:
            # Update last_login
            try:
                user = User.objects.get(email__iexact=email)
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
            except User.DoesNotExist:
                pass

        return response


# ─── Logout ───────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    POST /api/auth/logout/
    Blacklists the refresh token so it can't be reused.
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
    except TokenError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ─── Profile ──────────────────────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/  → return current user's profile
    PATCH /api/auth/profile/ → update username, name, bio, phone, avatar
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)


# ─── Change Password ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    POST /api/auth/change-password/
    Validates old password, then sets new hashed password.
    Blacklists refresh token to force re-login.
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    user = request.user
    user.set_password(serializer.validated_data['new_password'])
    user.save()

    # Blacklist existing refresh token if provided
    refresh_token = request.data.get('refresh')
    if refresh_token:
        try:
            RefreshToken(refresh_token).blacklist()
        except TokenError:
            pass

    # Issue new tokens
    refresh = RefreshToken.for_user(user)
    return Response({
        "message": "Password changed successfully.",
        "tokens": {
            "access":  str(refresh.access_token),
            "refresh": str(refresh),
        }
    }, status=status.HTTP_200_OK)


# ─── Token Verify / Introspect ────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def verify_token(request):
    """
    GET /api/auth/verify/
    Used by other microservices to validate a Bearer token.
    """
    return Response({
        "valid": True,
        "user": {
            "id":          request.user.id,
            "email":       request.user.email,
            "username":    request.user.username,
            "is_verified": request.user.is_verified,
            "is_staff":    request.user.is_staff,
        }
    })


# ─── Health Check ─────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    return Response({"status": "ok", "service": "auth_service"})
