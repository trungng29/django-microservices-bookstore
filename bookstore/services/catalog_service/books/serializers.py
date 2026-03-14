from rest_framework import serializers
from .models import Author, Publisher, Category, Book, BookAuthor, BookCategory, BookPrice, BookImage


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Author
        fields = ['id', 'name', 'slug', 'bio', 'avatar', 'nationality',
                  'birth_date', 'avg_rating', 'total_books']
        read_only_fields = ['id', 'slug', 'avg_rating', 'total_books']


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Publisher
        fields = ['id', 'name', 'slug', 'website', 'country', 'logo']
        read_only_fields = ['id', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model  = Category
        fields = ['id', 'name', 'slug', 'icon', 'parent', 'sort_order', 'children']
        read_only_fields = ['id', 'slug']

    def get_children(self, obj):
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class BookPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BookPrice
        fields = ['id', 'original_price', 'sale_price', 'discount_pct',
                  'valid_from', 'valid_to', 'is_active']
        read_only_fields = ['id', 'discount_pct']


class BookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BookImage
        fields = ['id', 'image', 'alt_text', 'sort_order']


# ── Book list (lightweight) ────────────────────────────────────────────────────
class BookListSerializer(serializers.ModelSerializer):
    authors       = serializers.SerializerMethodField()
    current_price = serializers.SerializerMethodField()
    primary_category = serializers.SerializerMethodField()

    class Meta:
        model  = Book
        fields = ['id', 'title', 'slug', 'cover_image', 'language', 'book_format',
                  'avg_rating', 'total_reviews', 'total_sold', 'in_stock',
                  'is_featured', 'is_bestseller', 'authors', 'current_price',
                  'primary_category', 'shop_id', 'created_at']

    def get_authors(self, obj):
        return [
            {'id': ba.author.id, 'name': ba.author.name, 'role': ba.role}
            for ba in obj.book_authors.select_related('author').order_by('sort_order')
        ]

    def get_current_price(self, obj):
        price = obj.current_price
        if price:
            return {
                'original': str(price.original_price),
                'sale':     str(price.sale_price),
                'discount': price.discount_pct,
            }
        return None

    def get_primary_category(self, obj):
        bc = obj.book_categories.filter(is_primary=True).select_related('category').first()
        if bc:
            return {'id': bc.category.id, 'name': bc.category.name}
        bc = obj.book_categories.select_related('category').first()
        return {'id': bc.category.id, 'name': bc.category.name} if bc else None


# ── Book detail (full) ─────────────────────────────────────────────────────────
class BookDetailSerializer(BookListSerializer):
    prices     = BookPriceSerializer(many=True, read_only=True)
    images     = BookImageSerializer(many=True, read_only=True)
    publisher  = PublisherSerializer(read_only=True)
    categories = serializers.SerializerMethodField()

    class Meta(BookListSerializer.Meta):
        fields = BookListSerializer.Meta.fields + [
            'subtitle', 'isbn', 'description', 'pages', 'publish_date',
            'edition', 'weight', 'dimensions', 'publisher',
            'categories', 'prices', 'images', 'updated_at',
        ]

    def get_categories(self, obj):
        return [
            {'id': bc.category.id, 'name': bc.category.name, 'is_primary': bc.is_primary}
            for bc in obj.book_categories.select_related('category')
        ]


# ── Book Upload (seller) ───────────────────────────────────────────────────────
class BookUploadSerializer(serializers.ModelSerializer):
    """
    Seller dùng form này để tải sách lên.
    author_ids  : list[int] — ID của Author records đã tồn tại
    category_ids: list[int] — ID của Category records
    price       : decimal   — giá bán
    original_price: decimal — giá gốc
    """
    author_ids     = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, min_length=1,
        help_text='Bắt buộc ít nhất 1 tác giả'
    )
    category_ids   = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, min_length=1,
        help_text='Bắt buộc ít nhất 1 danh mục'
    )
    sale_price     = serializers.DecimalField(max_digits=12, decimal_places=2, write_only=True)
    original_price = serializers.DecimalField(max_digits=12, decimal_places=2, write_only=True)

    class Meta:
        model  = Book
        fields = [
            'id', 'title', 'subtitle', 'isbn', 'description',
            'pages', 'language', 'book_format', 'publish_date',
            'edition', 'weight', 'dimensions',
            'cover_image', 'publisher',
            'author_ids', 'category_ids',
            'sale_price', 'original_price',
            'stock_quantity',
        ]
        read_only_fields = ['id']

    def validate_author_ids(self, value):
        found = Author.objects.filter(id__in=value)
        if found.count() != len(value):
            missing = set(value) - set(found.values_list('id', flat=True))
            raise serializers.ValidationError(f"Author IDs không tồn tại: {missing}")
        return value

    def validate_category_ids(self, value):
        found = Category.objects.filter(id__in=value)
        if found.count() != len(value):
            missing = set(value) - set(found.values_list('id', flat=True))
            raise serializers.ValidationError(f"Category IDs không tồn tại: {missing}")
        return value

    def validate(self, attrs):
        sale = attrs.get('sale_price', 0)
        orig = attrs.get('original_price', 0)
        if sale > orig:
            raise serializers.ValidationError(
                {"sale_price": "Giá bán không được cao hơn giá gốc."}
            )
        return attrs

    def create(self, validated_data):
        from django.utils import timezone
        author_ids     = validated_data.pop('author_ids')
        category_ids   = validated_data.pop('category_ids')
        sale_price     = validated_data.pop('sale_price')
        original_price = validated_data.pop('original_price')

        # shop_id được inject từ view (request.user_id / request context)
        book = Book.objects.create(**validated_data)

        # BookAuthor
        for i, aid in enumerate(author_ids):
            BookAuthor.objects.create(
                book=book,
                author_id=aid,
                role='author',
                sort_order=i,
            )

        # BookCategory
        for i, cid in enumerate(category_ids):
            BookCategory.objects.create(
                book=book,
                category_id=cid,
                is_primary=(i == 0),
            )

        # BookPrice
        BookPrice.objects.create(
            book=book,
            original_price=original_price,
            sale_price=sale_price,
            valid_from=timezone.now(),
            is_active=True,
            created_by=self.context['request_user_id'],
        )

        return book
