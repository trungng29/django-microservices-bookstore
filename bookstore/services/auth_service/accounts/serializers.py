import re
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

# ─── Validators ───────────────────────────────────────────────────────────────

def validate_username(value):
    if len(value) < 3:
        raise serializers.ValidationError("Username must be at least 3 characters.")
    if len(value) > 50:
        raise serializers.ValidationError("Username must not exceed 50 characters.")
    if not re.match(r'^[a-zA-Z0-9_.-]+$', value):
        raise serializers.ValidationError(
            "Username may only contain letters, numbers, underscores, hyphens, and dots."
        )
    if value.startswith('.') or value.endswith('.'):
        raise serializers.ValidationError("Username cannot start or end with a dot.")
    if User.objects.filter(username__iexact=value).exists():
        raise serializers.ValidationError("This username is already taken.")
    return value.lower()


def validate_phone(value):
    if value and not re.match(r'^\+?[0-9]{9,15}$', value):
        raise serializers.ValidationError("Enter a valid phone number (9–15 digits, optional +).")
    return value


# ─── Register ─────────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, label="Confirm password")
    phone     = serializers.CharField(required=False, allow_blank=True, validators=[validate_phone])

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'password', 'password2']
        read_only_fields = ['id']

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_username(self, value):
        return validate_username(value)

    def validate_password(self, value):
        # Django's built-in validators (length, common, similarity)
        validate_password(value)
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one digit.")
        if not re.search(r'[^a-zA-Z0-9]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ─── JWT Token (enriched payload) ─────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Extra claims embedded in JWT payload
        token['username']    = user.username
        token['email']       = user.email
        token['is_verified'] = user.is_verified
        token['full_name']   = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Append user profile data in login response
        data['user'] = UserProfileSerializer(self.user).data
        return data


# ─── Profile ──────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    full_name   = serializers.CharField(read_only=True)
    avatar_url  = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone', 'bio', 'avatar_url',
            'is_verified', 'date_joined', 'last_login',
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login', 'is_verified']

    def get_avatar_url(self, obj):
        request = self.context.get('request')
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None


class UpdateProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    phone    = serializers.CharField(required=False, allow_blank=True, validators=[validate_phone])

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'bio', 'avatar']

    def validate_username(self, value):
        if value == self.instance.username:
            return value
        return validate_username(value)


# ─── Change Password ──────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password  = serializers.CharField(required=True, write_only=True)
    new_password  = serializers.CharField(required=True, write_only=True, min_length=8)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Must contain at least one uppercase letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Must contain at least one digit.")
        if not re.search(r'[^a-zA-Z0-9]', value):
            raise serializers.ValidationError("Must contain at least one special character.")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({"new_password": "New password must be different from old password."})
        return attrs
