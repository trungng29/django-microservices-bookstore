from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """
    Đánh giá sách. Chỉ cho phép review nếu đã mua (order_id + order_item_id).
    user_id, book_id, order_id là external FKs.
    """
    # External FKs
    user_id       = models.BigIntegerField(db_index=True)
    book_id       = models.BigIntegerField(db_index=True)
    shop_id       = models.BigIntegerField(db_index=True)
    order_id      = models.BigIntegerField(null=True, blank=True, help_text='FK to order_service.orders')
    order_item_id = models.BigIntegerField(null=True, blank=True)

    # Snapshot (tránh phụ thuộc catalog_service khi display)
    book_title    = models.CharField(max_length=300, blank=True)
    book_cover    = models.URLField(blank=True)
    user_name     = models.CharField(max_length=100, blank=True)
    user_avatar   = models.URLField(blank=True)

    rating        = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title         = models.CharField(max_length=200, blank=True)
    content       = models.TextField(blank=True)

    # Phân loại đánh giá chi tiết
    quality_rating   = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    content_rating   = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    delivery_rating  = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])

    # Media
    images           = models.JSONField(default=list, blank=True, help_text='List of image URLs')

    # Status
    is_verified      = models.BooleanField(default=False, help_text='Verified purchase')
    is_approved      = models.BooleanField(default=True)
    is_featured      = models.BooleanField(default=False)
    helpful_count    = models.PositiveIntegerField(default=0)
    unhelpful_count  = models.PositiveIntegerField(default=0)

    # Admin
    admin_reply      = models.TextField(blank=True)
    admin_reply_at   = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'reviews'
        unique_together = ('user_id', 'book_id', 'order_item_id')
        ordering        = ['-created_at']
        indexes         = [
            models.Index(fields=['book_id', 'is_approved']),
            models.Index(fields=['user_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"Review {self.rating}★ on book {self.book_id} by user {self.user_id}"


class ReviewHelpful(models.Model):
    """Người dùng vote helpful/unhelpful cho review."""
    review     = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpful_votes')
    user_id    = models.BigIntegerField(db_index=True)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'review_helpful_votes'
        unique_together = ('review', 'user_id')


class Wishlist(models.Model):
    """
    Danh sách yêu thích. user_id và book_id là external FKs.
    """
    user_id    = models.BigIntegerField(db_index=True)
    book_id    = models.BigIntegerField(db_index=True)
    shop_id    = models.BigIntegerField(db_index=True)

    # Snapshot để hiển thị không cần gọi catalog_service
    book_title  = models.CharField(max_length=300, blank=True)
    book_cover  = models.URLField(blank=True)
    book_price  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    note        = models.CharField(max_length=200, blank=True)
    added_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'wishlists'
        unique_together = ('user_id', 'book_id')
        indexes         = [models.Index(fields=['user_id'])]

    def __str__(self):
        return f"User {self.user_id} wishlisted book {self.book_id}"


class Coupon(models.Model):
    """
    Mã giảm giá. Dùng chung cho toàn hệ thống hoặc riêng shop.
    shop_id=None có nghĩa là platform-wide coupon.
    """
    TYPE_CHOICES = [
        ('percentage', 'Percentage off'),
        ('fixed',      'Fixed amount off'),
        ('shipping',   'Free shipping'),
    ]

    SCOPE_CHOICES = [
        ('platform', 'Platform-wide'),
        ('shop',     'Shop specific'),
        ('category', 'Category specific'),
        ('book',     'Book specific'),
    ]

    code          = models.CharField(max_length=50, unique=True)
    description   = models.CharField(max_length=200, blank=True)
    coupon_type   = models.CharField(max_length=15, choices=TYPE_CHOICES)
    scope         = models.CharField(max_length=15, choices=SCOPE_CHOICES, default='platform')

    # External FK (optional)
    shop_id       = models.BigIntegerField(null=True, blank=True, db_index=True)
    category_id   = models.BigIntegerField(null=True, blank=True)
    book_id       = models.BigIntegerField(null=True, blank=True)
    created_by    = models.BigIntegerField(help_text='FK to auth_service.users')

    value         = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    min_order     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_discount  = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True,
                                        help_text='Max discount cap for percentage coupons')
    max_uses      = models.PositiveIntegerField(null=True, blank=True, help_text='None = unlimited')
    max_uses_per_user = models.PositiveSmallIntegerField(default=1)
    used_count    = models.PositiveIntegerField(default=0)

    valid_from    = models.DateTimeField()
    expires_at    = models.DateTimeField(null=True, blank=True)
    is_active     = models.BooleanField(default=True)

    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'coupons'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active', 'expires_at']),
        ]

    def __str__(self):
        return f"Coupon {self.code} — {self.value} ({self.coupon_type})"

    @property
    def is_expired(self):
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    @property
    def is_valid(self):
        if not self.is_active or self.is_expired:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True


class CouponUsage(models.Model):
    """Lịch sử dùng coupon của từng user cho từng đơn hàng."""
    coupon     = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user_id    = models.BigIntegerField(db_index=True)
    order_id   = models.BigIntegerField(unique=True, help_text='FK to order_service.orders')
    discount_applied = models.DecimalField(max_digits=12, decimal_places=2)
    used_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'coupon_usages'
        indexes  = [models.Index(fields=['user_id', 'coupon'])]

    def __str__(self):
        return f"Coupon {self.coupon.code} used by user {self.user_id} on order {self.order_id}"
