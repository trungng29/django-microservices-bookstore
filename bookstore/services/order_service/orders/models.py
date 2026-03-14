from django.db import models
from django.core.validators import MinValueValidator
import uuid


class Address(models.Model):
    """
    Địa chỉ giao hàng của người dùng.
    user_id là external FK tới auth_service.
    Snapshot address vào OrderShippingAddress khi đặt hàng
    để address không bị thay đổi ảnh hưởng đến đơn cũ.
    """
    user_id    = models.BigIntegerField(db_index=True, help_text='FK to auth_service.users')
    full_name  = models.CharField(max_length=150)
    phone      = models.CharField(max_length=20)
    street     = models.TextField()
    district   = models.CharField(max_length=100, blank=True)
    city       = models.CharField(max_length=100)
    province   = models.CharField(max_length=100, blank=True)
    country    = models.CharField(max_length=100, default='Vietnam')
    postal_code = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'addresses'
        indexes  = [models.Index(fields=['user_id'])]

    def __str__(self):
        return f"{self.full_name} — {self.street}, {self.city}"


class Cart(models.Model):
    """
    Giỏ hàng — 1 user chỉ có 1 cart active.
    book_id, shop_id là external FKs tới catalog_service và shop_service.
    """
    user_id    = models.BigIntegerField(unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'carts'

    def __str__(self):
        return f"Cart of user {self.user_id}"

    @property
    def total_items(self):
        return self.items.aggregate(models.Sum('quantity'))['quantity__sum'] or 0

    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart      = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')

    # External FKs — snapshot title & price tại thời điểm thêm vào giỏ
    book_id      = models.BigIntegerField(db_index=True)
    shop_id      = models.BigIntegerField(db_index=True)
    book_title   = models.CharField(max_length=300)
    book_cover   = models.URLField(blank=True)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])

    quantity     = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    added_at     = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'cart_items'
        unique_together = ('cart', 'book_id')

    def __str__(self):
        return f"{self.book_title} x{self.quantity}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class Order(models.Model):
    """
    Đơn hàng. Snapshot toàn bộ thông tin giá, địa chỉ tại thời điểm đặt.
    Không tham chiếu sang DB khác sau khi order được tạo.
    """
    STATUS_CHOICES = [
        ('pending',    'Pending'),        # Chờ xác nhận
        ('confirmed',  'Confirmed'),      # Shop xác nhận
        ('processing', 'Processing'),     # Đang đóng gói
        ('shipped',    'Shipped'),        # Đang giao
        ('delivered',  'Delivered'),      # Đã giao
        ('cancelled',  'Cancelled'),      # Đã huỷ
        ('refunded',   'Refunded'),       # Đã hoàn tiền
        ('returned',   'Returned'),       # Trả hàng
    ]

    SOURCE_CHOICES = [
        ('web',     'Website'),
        ('mobile',  'Mobile App'),
        ('api',     'API'),
    ]

    # External FKs
    user_id  = models.BigIntegerField(db_index=True)
    shop_id  = models.BigIntegerField(db_index=True)

    order_number = models.CharField(
        max_length=30, unique=True, blank=True,
        help_text='Human-readable: BV-20240115-XXXX'
    )

    status   = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    source   = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='web')

    # Snapshot địa chỉ giao hàng (không dùng FK để tránh thay đổi sau)
    shipping_full_name  = models.CharField(max_length=150)
    shipping_phone      = models.CharField(max_length=20)
    shipping_street     = models.TextField()
    shipping_district   = models.CharField(max_length=100, blank=True)
    shipping_city       = models.CharField(max_length=100)
    shipping_country    = models.CharField(max_length=100, default='Vietnam')

    # Tài chính (snapshot tại thời điểm đặt)
    subtotal      = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    shipping_fee  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount      = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total         = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])

    # Coupon (nếu có)
    coupon_code   = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    note          = models.TextField(blank=True, help_text='Note from customer')
    admin_note    = models.TextField(blank=True, help_text='Internal note')

    # Timestamps
    ordered_at    = models.DateTimeField(auto_now_add=True)
    confirmed_at  = models.DateTimeField(null=True, blank=True)
    shipped_at    = models.DateTimeField(null=True, blank=True)
    delivered_at  = models.DateTimeField(null=True, blank=True)
    cancelled_at  = models.DateTimeField(null=True, blank=True)

    # Tracking
    tracking_number  = models.CharField(max_length=100, blank=True)
    shipping_carrier = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-ordered_at']
        indexes  = [
            models.Index(fields=['user_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['ordered_at']),
        ]

    def __str__(self):
        return self.order_number or f"Order #{self.pk}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.utils import timezone
            date_str = timezone.now().strftime('%Y%m%d')
            uid      = str(uuid.uuid4())[:6].upper()
            self.order_number = f"BV-{date_str}-{uid}"
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """
    Dòng sản phẩm trong đơn hàng. Snapshot đầy đủ thông tin sách
    để đơn hàng không bị ảnh hưởng khi sách thay đổi giá / bị xoá.
    """
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')

    # Snapshot từ catalog_service
    book_id      = models.BigIntegerField()
    shop_id      = models.BigIntegerField()
    book_title   = models.CharField(max_length=300)
    book_isbn    = models.CharField(max_length=13, blank=True)
    book_cover   = models.URLField(blank=True)
    author_names = models.CharField(max_length=300, blank=True)

    unit_price   = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    original_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    quantity     = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    subtotal     = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])

    # Trạng thái riêng của từng item (hỗ trợ partial refund)
    STATUS_CHOICES = [
        ('active',    'Active'),
        ('cancelled', 'Cancelled'),
        ('refunded',  'Refunded'),
        ('returned',  'Returned'),
    ]
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'order_items'
        indexes  = [models.Index(fields=['book_id'])]

    def __str__(self):
        return f"{self.book_title} x{self.quantity} in {self.order}"

    def save(self, *args, **kwargs):
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusHistory(models.Model):
    """Audit log các lần thay đổi trạng thái đơn hàng."""
    order       = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=15, blank=True)
    to_status   = models.CharField(max_length=15)
    changed_by  = models.BigIntegerField(null=True, help_text='FK to auth_service.users')
    note        = models.TextField(blank=True)
    changed_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_status_history'
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.order} : {self.from_status} → {self.to_status}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cod',          'Cash on Delivery'),
        ('bank_transfer','Bank Transfer'),
        ('momo',         'MoMo'),
        ('vnpay',        'VNPay'),
        ('zalopay',      'ZaloPay'),
        ('stripe',       'Stripe'),
        ('paypal',       'PayPal'),
    ]

    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('processing','Processing'),
        ('completed', 'Completed'),
        ('failed',    'Failed'),
        ('refunded',  'Refunded'),
        ('cancelled', 'Cancelled'),
    ]

    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method         = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status         = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    amount         = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])

    # Payment gateway data
    transaction_id   = models.CharField(max_length=200, blank=True, unique=True, null=True)
    gateway_response = models.JSONField(default=dict, blank=True, help_text='Raw response from payment gateway')
    gateway_ref      = models.CharField(max_length=200, blank=True)

    paid_at          = models.DateTimeField(null=True, blank=True)
    refunded_at      = models.DateTimeField(null=True, blank=True)
    refund_amount    = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    refund_reason    = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        indexes  = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Payment {self.transaction_id or self.pk} for {self.order}"
