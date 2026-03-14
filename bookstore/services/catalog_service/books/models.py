from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator


class Author(models.Model):
    """
    Tác giả sách. Không kết nối trực tiếp với User vì tác giả là dữ liệu
    catalogue, không phải account. Nếu cần liên kết: dùng author_user_id (external FK).
    """
    name        = models.CharField(max_length=200)
    slug        = models.SlugField(max_length=220, unique=True, blank=True)
    bio         = models.TextField(blank=True)
    avatar      = models.ImageField(upload_to='authors/', blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True)
    birth_date  = models.DateField(null=True, blank=True)
    death_date  = models.DateField(null=True, blank=True)
    website     = models.URLField(blank=True)
    avg_rating  = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_books = models.PositiveIntegerField(default=0)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'authors'
        ordering = ['name']
        indexes  = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Publisher(models.Model):
    name       = models.CharField(max_length=200, unique=True)
    slug       = models.SlugField(max_length=220, unique=True, blank=True)
    website    = models.URLField(blank=True)
    email      = models.EmailField(blank=True)
    country    = models.CharField(max_length=100, blank=True)
    logo       = models.ImageField(upload_to='publishers/', blank=True, null=True)
    founded_at = models.PositiveIntegerField(null=True, blank=True, help_text='Year founded')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'publishers'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    Danh mục đệ quy (self-referential). parent=None là root category.
    Ví dụ: Fiction > Science Fiction > Cyberpunk
    """
    parent      = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
    )
    name        = models.CharField(max_length=100)
    slug        = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon        = models.CharField(max_length=10, blank=True, help_text='Emoji icon')
    sort_order  = models.PositiveSmallIntegerField(default=0)
    is_active   = models.BooleanField(default=True)

    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'categories'
        ordering  = ['sort_order', 'name']
        verbose_name_plural = 'categories'
        indexes   = [models.Index(fields=['slug'])]

    def __str__(self):
        return self.full_path

    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    """
    Thực thể trung tâm của Catalog Service.
    shop_id là external FK (không JOIN trực tiếp sang shop_service DB).
    """
    LANGUAGE_CHOICES = [
        ('vi', 'Tiếng Việt'),
        ('en', 'English'),
        ('fr', 'Français'),
        ('ja', '日本語'),
        ('zh', '中文'),
        ('ko', '한국어'),
        ('de', 'Deutsch'),
        ('es', 'Español'),
    ]

    FORMAT_CHOICES = [
        ('paperback', 'Paperback'),
        ('hardcover', 'Hardcover'),
        ('ebook',     'E-Book'),
        ('audiobook', 'Audiobook'),
    ]

    # External FKs (no DB-level FK constraint across services)
    shop_id       = models.BigIntegerField(db_index=True, help_text='FK to shop_service.shops')

    publisher     = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True, related_name='books')
    title         = models.CharField(max_length=300)
    slug          = models.SlugField(max_length=320, unique=True, blank=True)
    subtitle      = models.CharField(max_length=300, blank=True)
    isbn          = models.CharField(max_length=13, unique=True, blank=True, null=True)
    description   = models.TextField(blank=True)
    pages         = models.PositiveIntegerField(null=True, blank=True)
    language      = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='vi')
    book_format   = models.CharField(max_length=15, choices=FORMAT_CHOICES, default='paperback')
    publish_date  = models.DateField(null=True, blank=True)
    edition       = models.PositiveSmallIntegerField(default=1)
    weight        = models.PositiveIntegerField(null=True, blank=True, help_text='Grams')
    dimensions    = models.CharField(max_length=50, blank=True, help_text='W x H x D mm')

    # Media
    cover_image   = models.ImageField(upload_to='books/covers/', blank=True, null=True)
    cover_thumb   = models.ImageField(upload_to='books/thumbs/', blank=True, null=True)
    sample_pdf    = models.FileField(upload_to='books/samples/', blank=True, null=True)

    # Stats (denormalized, updated by signals)
    avg_rating      = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews   = models.PositiveIntegerField(default=0)
    total_sold      = models.PositiveIntegerField(default=0)
    stock_quantity  = models.IntegerField(default=0)

    # Flags
    is_active       = models.BooleanField(default=True)
    is_featured     = models.BooleanField(default=False)
    is_bestseller   = models.BooleanField(default=False)

    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'books'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['slug']),
            models.Index(fields=['isbn']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['avg_rating']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)
            self.slug = f"{base}-{self.isbn or self.pk or 'book'}"
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        """Trả về BookPrice đang active hiện tại."""
        from django.utils import timezone
        now = timezone.now()
        return self.prices.filter(
            is_active=True,
            valid_from__lte=now,
        ).filter(
            models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=now)
        ).order_by('-valid_from').first()

    @property
    def in_stock(self):
        return self.stock_quantity > 0


class BookAuthor(models.Model):
    """Bảng trung gian: 1 cuốn sách có thể có nhiều tác giả với vai trò khác nhau."""
    ROLE_CHOICES = [
        ('author',      'Author'),
        ('co_author',   'Co-Author'),
        ('editor',      'Editor'),
        ('translator',  'Translator'),
        ('illustrator', 'Illustrator'),
        ('foreword',    'Foreword by'),
    ]

    book       = models.ForeignKey(Book,   on_delete=models.CASCADE, related_name='book_authors')
    author     = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='book_authors')
    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='author')
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table        = 'book_authors'
        unique_together = ('book', 'author', 'role')
        ordering        = ['sort_order']

    def __str__(self):
        return f"{self.author.name} — {self.get_role_display()} of '{self.book.title}'"


class BookCategory(models.Model):
    """Bảng trung gian: 1 sách có thể thuộc nhiều danh mục."""
    book       = models.ForeignKey(Book,     on_delete=models.CASCADE, related_name='book_categories')
    category   = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='book_categories')
    is_primary = models.BooleanField(default=False, help_text='Primary category for breadcrumb')

    class Meta:
        db_table        = 'book_categories'
        unique_together = ('book', 'category')

    def __str__(self):
        return f"'{self.book.title}' in '{self.category.name}'"


class BookPrice(models.Model):
    """
    Lịch sử giá. Cho phép lên lịch giảm giá trước (valid_from/valid_to).
    Chỉ 1 price record is_active=True tại 1 thời điểm cho mỗi book.
    """
    book           = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='prices')
    original_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    sale_price     = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    discount_pct   = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        help_text='Auto-calculated discount percentage'
    )
    valid_from     = models.DateTimeField()
    valid_to       = models.DateTimeField(null=True, blank=True)
    is_active      = models.BooleanField(default=True)
    created_by     = models.BigIntegerField(help_text='FK to auth_service.users')

    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'book_prices'
        ordering = ['-valid_from']
        indexes  = [
            models.Index(fields=['book', 'is_active']),
            models.Index(fields=['valid_from', 'valid_to']),
        ]

    def save(self, *args, **kwargs):
        if self.original_price and self.sale_price:
            diff = self.original_price - self.sale_price
            self.discount_pct = int((diff / self.original_price) * 100)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.book.title} — {self.sale_price} ({self.discount_pct}% off)"


class BookImage(models.Model):
    """Ảnh bổ sung (gallery) cho sách."""
    book       = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='images')
    image      = models.ImageField(upload_to='books/gallery/')
    alt_text   = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = 'book_images'
        ordering = ['sort_order']
