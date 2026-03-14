from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Shop(models.Model):
    """
    Gian hàng của người bán. owner_id là external FK tới auth_service.users.
    Mỗi user có thể sở hữu nhiều shop (marketplace model).
    """
    STATUS_CHOICES = [
        ('pending',   'Pending Review'),
        ('active',    'Active'),
        ('suspended', 'Suspended'),
        ('closed',    'Closed'),
    ]

    # External FK — không dùng ForeignKey Django thật
    owner_id      = models.BigIntegerField(db_index=True, help_text='FK to auth_service.users')

    name          = models.CharField(max_length=200, unique=True)
    slug          = models.SlugField(max_length=220, unique=True, blank=True)
    description   = models.TextField(blank=True)
    logo          = models.ImageField(upload_to='shops/logos/', blank=True, null=True)
    banner        = models.ImageField(upload_to='shops/banners/', blank=True, null=True)
    address       = models.TextField(blank=True)
    city          = models.CharField(max_length=100, blank=True)
    country       = models.CharField(max_length=100, default='Vietnam')
    phone         = models.CharField(max_length=20, blank=True)
    email         = models.EmailField(blank=True)
    website       = models.URLField(blank=True)

    # Stats (denormalized)
    rating        = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.PositiveIntegerField(default=0)
    total_sales   = models.PositiveIntegerField(default=0)
    total_books   = models.PositiveIntegerField(default=0)

    # Status
    status        = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    is_verified   = models.BooleanField(default=False)
    is_featured   = models.BooleanField(default=False)

    # Policy
    return_policy    = models.TextField(blank=True)
    shipping_policy  = models.TextField(blank=True)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shops'
        ordering = ['-is_featured', '-rating']
        indexes  = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status == 'active'


class ShopFollower(models.Model):
    """Người dùng theo dõi shop. user_id là external FK."""
    shop       = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='followers')
    user_id    = models.BigIntegerField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'shop_followers'
        unique_together = ('shop', 'user_id')

    def __str__(self):
        return f"User {self.user_id} follows {self.shop.name}"


class ShopStaff(models.Model):
    """Nhân viên của shop (phân quyền nội bộ trong shop)."""
    ROLE_CHOICES = [
        ('manager',   'Manager'),
        ('staff',     'Staff'),
        ('warehouse', 'Warehouse'),
    ]

    shop       = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='staff')
    user_id    = models.BigIntegerField(db_index=True)
    role       = models.CharField(max_length=15, choices=ROLE_CHOICES, default='staff')
    is_active  = models.BooleanField(default=True)
    joined_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'shop_staff'
        unique_together = ('shop', 'user_id')

    def __str__(self):
        return f"{self.shop.name} — user {self.user_id} ({self.role})"


class ShopAddress(models.Model):
    """Địa chỉ kho/văn phòng của shop (có thể nhiều)."""
    shop         = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='addresses')
    label        = models.CharField(max_length=50, help_text='e.g. Main Warehouse, Hanoi Office')
    street       = models.TextField()
    district     = models.CharField(max_length=100, blank=True)
    city         = models.CharField(max_length=100)
    country      = models.CharField(max_length=100, default='Vietnam')
    is_primary   = models.BooleanField(default=False)
    phone        = models.CharField(max_length=20, blank=True)

    class Meta:
        db_table = 'shop_addresses'

    def __str__(self):
        return f"{self.shop.name} — {self.label}"
