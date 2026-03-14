import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()


# ── Validators ────────────────────────────────────────────────────────────────

def validate_username(value):
    if len(value) < 3:
        raise serializers.ValidationError("Username phải có ít nhất 3 ký tự.")
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise serializers.ValidationError("Username chỉ được chứa chữ, số, _ . -")
    if User.objects.filter(username__iexact=value).exists():
        raise serializers.ValidationError("Username này đã được sử dụng.")
    return value.lower()


# ── Register ──────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, label='Confirm password')
    role      = serializers.ChoiceField(
        choices=['customer', 'seller', 'author'],
        default='customer',
        write_only=True,
        help_text='customer | seller | author (admin không thể tự đăng ký)',
    )

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'password', 'password2', 'role']
        read_only_fields = ['id']

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email này đã được đăng ký.")
        return value

    def validate_username(self, value):
        return validate_username(value)

    def validate_password(self, value):
        validate_password(value)
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Phải có ít nhất 1 chữ HOA.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Phải có ít nhất 1 chữ số.")
        if not re.search(r'[^a-zA-Z0-9]', value):
            raise serializers.ValidationError("Phải có ít nhất 1 ký tự đặc biệt.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password2": "Mật khẩu không khớp."})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'customer')
        return User.objects.create_user(role=role, **validated_data)


# ── JWT (enriched payload) ────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Nhét roles + permissions vào JWT để các service khác đọc không cần gọi lại auth
        token['username']    = user.username
        token['email']       = user.email
        token['roles']       = user.roles                       # ['seller', 'author']
        token['primary_role'] = user.primary_role               # 'seller'
        token['permissions'] = user.get_all_permissions_flat()  # ['catalog:book:create', ...]
        token['is_verified'] = user.is_verified
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserProfileSerializer(self.user).data
        return data


# ── Profile ───────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    full_name    = serializers.CharField(read_only=True)
    roles        = serializers.ListField(read_only=True)
    primary_role = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name',
                  'full_name', 'phone', 'bio', 'avatar',
                  'roles', 'primary_role', 'is_verified', 'date_joined', 'last_login']
        read_only_fields = ['id', 'email', 'date_joined', 'last_login', 'is_verified',
                            'roles', 'primary_role']


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'phone', 'bio', 'avatar']


# ── Change Password ───────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(write_only=True)
    new_password  = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError("Mật khẩu hiện tại không đúng.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Phải có ít nhất 1 chữ HOA.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Phải có ít nhất 1 chữ số.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "Mật khẩu không khớp."})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "Mật khẩu mới phải khác mật khẩu cũ."})
        return attrs


# ── Seller Profile ────────────────────────────────────────────────────────────

class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        from accounts.models import SellerProfile
        model  = SellerProfile
        fields = ['id', 'business_name', 'business_type', 'tax_code',
                  'verify_status', 'verified_at', 'commission_rate',
                  'bank_name', 'bank_account', 'bank_owner',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'verify_status', 'verified_at', 'commission_rate']


# ── Author Profile ────────────────────────────────────────────────────────────

class AuthorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        from accounts.models import AuthorProfile
        model  = AuthorProfile
        fields = ['id', 'pen_name', 'nationality', 'biography', 'website',
                  'facebook', 'is_verified', 'catalog_author_id',
                  'royalty_rate', 'bank_name', 'bank_account', 'bank_owner',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'is_verified', 'catalog_author_id', 'royalty_rate']
