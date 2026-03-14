from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


# ══════════════════════════════════════════════════════════════════════════════
# ROLE & PERMISSION DEFINITIONS
# ══════════════════════════════════════════════════════════════════════════════

class Role(models.Model):
    """
    4 roles hệ thống:
      - customer   : Khách hàng mua sách
      - seller     : Nhà sách / người bán (sở hữu Shop, upload sách)
      - author     : Tác giả (có Author profile, xem doanh thu)
      - admin      : Quản trị viên nền tảng

    Role được gán vào JWT payload → các service đọc trực tiếp từ token,
    không cần gọi lại auth_service mỗi request.
    """
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('seller',   'Seller'),
        ('author',   'Author'),
        ('admin',    'Admin'),
    ]

    name        = models.CharField(max_length=20, unique=True, choices=ROLE_CHOICES)
    display_name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.display_name


class Permission(models.Model):
    """
    Fine-grained permissions theo format: service:resource:action
    Ví dụ:
      catalog:book:create
      catalog:book:read
      catalog:book:update
      catalog:book:delete
      shop:shop:create
      order:order:read_own
      order:order:read_all   (admin only)
      interaction:review:create
    """
    codename    = models.CharField(max_length=100, unique=True)
    name        = models.CharField(max_length=200)
    service     = models.CharField(max_length=30, help_text='catalog | shop | order | interaction | auth')
    resource    = models.CharField(max_length=50, help_text='book | shop | order | review | user ...')
    action      = models.CharField(max_length=30, help_text='create | read | read_own | update | delete | publish')
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'permissions'
        ordering = ['service', 'resource', 'action']

    def __str__(self):
        return f"{self.codename}"


class RolePermission(models.Model):
    """Gán Permission cho Role (M2M với extra field)."""
    role       = models.ForeignKey(Role,       on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='role_permissions')
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'role_permissions'
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} → {self.permission.codename}"


# ══════════════════════════════════════════════════════════════════════════════
# USER MODEL
# ══════════════════════════════════════════════════════════════════════════════

class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, role='customer', **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        if not username:
            raise ValueError('Username is required.')
        email = self.normalize_email(email)
        user  = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        # Gán role mặc định
        user.assign_role(role)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active',    True)
        user = self.create_user(email, username, password, role='admin', **extra_fields)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User. Role được lưu qua UserRole (M2M).
    Password: PBKDF2+SHA256 qua set_password().
    ID: BigAutoField (auto-increment).
    """
    email       = models.EmailField(unique=True, max_length=255)
    username    = models.CharField(unique=True, max_length=50)
    first_name  = models.CharField(max_length=50, blank=True)
    last_name   = models.CharField(max_length=50, blank=True)
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio         = models.TextField(blank=True, max_length=500)
    phone       = models.CharField(max_length=15, blank=True)

    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes  = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.username} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    # ── Role helpers ──────────────────────────────────────────────────────────

    def assign_role(self, role_name: str):
        """Gán role cho user. Tạo Role nếu chưa có."""
        role, _ = Role.objects.get_or_create(
            name=role_name,
            defaults={'display_name': role_name.title()}
        )
        UserRole.objects.get_or_create(user=self, role=role)

    def remove_role(self, role_name: str):
        UserRole.objects.filter(user=self, role__name=role_name).delete()

    @property
    def roles(self) -> list:
        """Trả về list tên role, e.g. ['seller', 'author']"""
        return list(self.user_roles.values_list('role__name', flat=True))

    @property
    def primary_role(self) -> str:
        """Role chính (ưu tiên: admin > seller > author > customer)."""
        priority = ['admin', 'seller', 'author', 'customer']
        for r in priority:
            if r in self.roles:
                return r
        return 'customer'

    def has_role(self, *role_names) -> bool:
        return bool(self.user_roles.filter(role__name__in=role_names).exists())

    def get_permissions_for_service(self, service: str) -> list:
        """Trả về list codename permissions của user cho một service cụ thể."""
        return list(
            RolePermission.objects.filter(
                role__user_roles__user=self,
                permission__service=service,
            ).values_list('permission__codename', flat=True).distinct()
        )

    def get_all_permissions_flat(self) -> list:
        """Tất cả permission codenames của user (dùng để nhét vào JWT)."""
        return list(
            RolePermission.objects.filter(
                role__user_roles__user=self
            ).values_list('permission__codename', flat=True).distinct()
        )


class UserRole(models.Model):
    """Bảng trung gian User ↔ Role. 1 user có thể có nhiều role (vd: seller + author)."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role       = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles')
    assigned_by = models.BigIntegerField(null=True, blank=True, help_text='admin user_id who assigned this')
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at  = models.DateTimeField(null=True, blank=True, help_text='Temporary role expiry')

    class Meta:
        db_table        = 'user_roles'
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} → {self.role.name}"

    @property
    def is_active(self):
        if self.expires_at:
            return timezone.now() < self.expires_at
        return True


# ══════════════════════════════════════════════════════════════════════════════
# SELLER / AUTHOR PROFILES  (extended info cho role đặc biệt)
# ══════════════════════════════════════════════════════════════════════════════

class SellerProfile(models.Model):
    """
    Profile riêng cho Seller. Lưu thông tin pháp lý / KYC.
    Tách khỏi User để không bloat bảng users.
    """
    VERIFY_STATUS = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name     = models.CharField(max_length=200, blank=True)
    business_type     = models.CharField(max_length=50, blank=True,
                                         help_text='individual | company | publisher')
    tax_code          = models.CharField(max_length=50, blank=True)
    id_card_number    = models.CharField(max_length=50, blank=True)
    id_card_front     = models.ImageField(upload_to='kyc/id_cards/', blank=True, null=True)
    id_card_back      = models.ImageField(upload_to='kyc/id_cards/', blank=True, null=True)
    business_license  = models.FileField(upload_to='kyc/licenses/', blank=True, null=True)

    verify_status     = models.CharField(max_length=15, choices=VERIFY_STATUS, default='pending')
    verified_at       = models.DateTimeField(null=True, blank=True)
    verified_by       = models.BigIntegerField(null=True, blank=True)
    reject_reason     = models.TextField(blank=True)

    # Bank info cho thanh toán
    bank_name         = models.CharField(max_length=100, blank=True)
    bank_account      = models.CharField(max_length=50, blank=True)
    bank_owner        = models.CharField(max_length=150, blank=True)

    # Giới hạn
    max_shops         = models.PositiveSmallIntegerField(default=3)
    commission_rate   = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                            help_text='Platform commission % per sale')

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'seller_profiles'

    def __str__(self):
        return f"Seller: {self.user.username}"

    @property
    def is_approved(self):
        return self.verify_status == 'approved'


class AuthorProfile(models.Model):
    """
    Profile riêng cho Author.
    author_id ở catalog_service.authors là external FK trỏ về đây.
    """
    user            = models.OneToOneField(User, on_delete=models.CASCADE, related_name='author_profile')

    # Liên kết tới catalog_service (external FK)
    catalog_author_id = models.BigIntegerField(
        null=True, blank=True,
        help_text='FK to catalog_service.authors — set sau khi admin tạo Author record bên catalog'
    )

    pen_name        = models.CharField(max_length=200, blank=True, help_text='Bút danh')
    nationality     = models.CharField(max_length=100, blank=True)
    biography       = models.TextField(blank=True)
    website         = models.URLField(blank=True)
    facebook        = models.URLField(blank=True)

    is_verified     = models.BooleanField(default=False, help_text='Tác giả đã được xác minh danh tính')
    verified_at     = models.DateTimeField(null=True, blank=True)

    # Royalty
    royalty_rate    = models.DecimalField(max_digits=5, decimal_places=2, default=10.00,
                                          help_text='Royalty % trên mỗi cuốn bán được')
    bank_name       = models.CharField(max_length=100, blank=True)
    bank_account    = models.CharField(max_length=50, blank=True)
    bank_owner      = models.CharField(max_length=150, blank=True)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'author_profiles'

    def __str__(self):
        return f"Author: {self.pen_name or self.user.username}"


# ══════════════════════════════════════════════════════════════════════════════
# AUDIT
# ══════════════════════════════════════════════════════════════════════════════

class LoginAttempt(models.Model):
    email      = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True)
    success    = models.BooleanField(default=False)
    timestamp  = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'login_attempts'
        indexes  = [models.Index(fields=['email', 'timestamp'])]
