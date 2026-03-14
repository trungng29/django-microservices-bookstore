from django.db.models import Q
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.pagination import PageNumberPagination

from .models import Author, Publisher, Category, Book, BookAuthor, BookCategory, BookPrice
from .serializers import (
    AuthorSerializer, PublisherSerializer, CategorySerializer,
    BookListSerializer, BookDetailSerializer, BookUploadSerializer,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_info(request):
    """Đọc user info từ JWT middleware (đã được inject bởi JWTAuthMiddleware)."""
    return {
        'user_id':     getattr(request, 'user_id', None),
        'roles':       getattr(request, 'user_roles', []),
        'permissions': getattr(request, 'user_permissions', []),
        'authed':      getattr(request, 'is_authenticated', False),
    }

def has_permission(request, codename):
    perms = getattr(request, 'user_permissions', [])
    return codename in perms

def require_permission_response(codename):
    return Response(
        {"error": f"Cần quyền: {codename}", "code": "forbidden"},
        status=status.HTTP_403_FORBIDDEN,
    )


# ── Pagination ────────────────────────────────────────────────────────────────

class BookPagination(PageNumberPagination):
    page_size            = 20
    page_size_query_param = 'page_size'
    max_page_size        = 100


# ══════════════════════════════════════════════════════════════════════════════
# CATEGORY
# ══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """GET /api/catalog/categories/ — cây danh mục (chỉ root)"""
    roots = Category.objects.filter(parent=None, is_active=True).prefetch_related('children')
    return Response(CategorySerializer(roots, many=True).data)


# ══════════════════════════════════════════════════════════════════════════════
# AUTHOR
# ══════════════════════════════════════════════════════════════════════════════

class AuthorListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/catalog/authors/  — public
    POST /api/catalog/authors/  — seller hoặc admin (catalog:author:create)
    """
    serializer_class = AuthorSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields   = ['name', 'nationality']
    ordering_fields = ['name', 'avg_rating', 'total_books']
    ordering        = ['name']
    queryset        = Author.objects.all()

    def create(self, request, *args, **kwargs):
        if not has_permission(request, 'catalog:author:create'):
            return require_permission_response('catalog:author:create')
        return super().create(request, *args, **kwargs)


class AuthorDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/catalog/authors/<id>/
    PATCH /api/catalog/authors/<id>/ — author (update_own) hoặc admin (update_all)
    """
    serializer_class   = AuthorSerializer
    permission_classes = [AllowAny]
    queryset           = Author.objects.all()

    def update(self, request, *args, **kwargs):
        if not (has_permission(request, 'catalog:author:update_own') or
                has_permission(request, 'catalog:author:update_all')):
            return require_permission_response('catalog:author:update_own')
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# PUBLISHER
# ══════════════════════════════════════════════════════════════════════════════

class PublisherListCreateView(generics.ListCreateAPIView):
    serializer_class   = PublisherSerializer
    permission_classes = [AllowAny]
    queryset           = Publisher.objects.all()

    def create(self, request, *args, **kwargs):
        if not has_permission(request, 'catalog:publisher:manage'):
            return require_permission_response('catalog:publisher:manage')
        return super().create(request, *args, **kwargs)


# ══════════════════════════════════════════════════════════════════════════════
# BOOK — list / search
# ══════════════════════════════════════════════════════════════════════════════

class BookListView(generics.ListAPIView):
    """
    GET /api/catalog/books/
    Params: q, category, author, shop_id, language, format,
            min_price, max_price, featured, bestseller, ordering
    """
    serializer_class   = BookListSerializer
    permission_classes = [AllowAny]
    pagination_class   = BookPagination

    def get_queryset(self):
        qs = (Book.objects
              .filter(is_active=True)
              .select_related('publisher')
              .prefetch_related('book_authors__author', 'book_categories__category', 'prices'))

        p = self.request.query_params

        if q := p.get('q'):
            qs = qs.filter(
                Q(title__icontains=q) |
                Q(book_authors__author__name__icontains=q) |
                Q(isbn__icontains=q)
            ).distinct()

        if cat := p.get('category'):
            qs = qs.filter(book_categories__category__slug=cat)

        if author := p.get('author'):
            qs = qs.filter(book_authors__author__slug=author)

        if shop_id := p.get('shop_id'):
            qs = qs.filter(shop_id=shop_id)

        if lang := p.get('language'):
            qs = qs.filter(language=lang)

        if fmt := p.get('format'):
            qs = qs.filter(book_format=fmt)

        if p.get('featured') == '1':
            qs = qs.filter(is_featured=True)

        if p.get('bestseller') == '1':
            qs = qs.filter(is_bestseller=True)

        ordering = p.get('ordering', '-created_at')
        allowed  = ['created_at', '-created_at', 'avg_rating', '-avg_rating',
                    'total_sold', '-total_sold']
        if ordering in allowed:
            qs = qs.order_by(ordering)

        return qs


# ══════════════════════════════════════════════════════════════════════════════
# BOOK — detail
# ══════════════════════════════════════════════════════════════════════════════

@api_view(['GET'])
@permission_classes([AllowAny])
def book_detail(request, slug):
    """GET /api/catalog/books/<slug>/"""
    try:
        book = (Book.objects
                .filter(slug=slug, is_active=True)
                .select_related('publisher')
                .prefetch_related('book_authors__author', 'book_categories__category',
                                  'prices', 'images')
                .get())
    except Book.DoesNotExist:
        return Response({"error": "Sách không tồn tại."}, status=status.HTTP_404_NOT_FOUND)
    return Response(BookDetailSerializer(book).data)


# ══════════════════════════════════════════════════════════════════════════════
# BOOK — upload (seller only)
# ══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])   # Auth checked manually via JWT middleware
def book_upload(request):
    """
    POST /api/catalog/books/upload/
    Permission: catalog:book:create  (seller role)
    Hỗ trợ multipart/form-data (với ảnh bìa) và JSON.
    """
    if not getattr(request, 'is_authenticated', False):
        return Response({"error": "Vui lòng đăng nhập."}, status=status.HTTP_401_UNAUTHORIZED)

    if not has_permission(request, 'catalog:book:create'):
        return Response(
            {"error": "Chỉ Seller mới có thể đăng sách.", "code": "forbidden"},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Gắn shop_id từ request header (frontend gửi kèm)
    shop_id = request.data.get('shop_id') or request.META.get('HTTP_X_SHOP_ID')
    if not shop_id:
        return Response({"error": "Thiếu shop_id."}, status=status.HTTP_400_BAD_REQUEST)

    # Parse author_ids và category_ids từ form data (có thể là string "1,2,3")
    data = request.data.copy()
    for field in ['author_ids', 'category_ids']:
        val = data.get(field)
        if isinstance(val, str):
            try:
                data[field] = [int(x.strip()) for x in val.split(',') if x.strip()]
            except ValueError:
                return Response({"error": f"{field} phải là danh sách số nguyên."},
                                status=status.HTTP_400_BAD_REQUEST)

    serializer = BookUploadSerializer(
        data=data,
        context={'request_user_id': getattr(request, 'user_id', 0)}
    )

    if not serializer.is_valid():
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    book = serializer.save(shop_id=int(shop_id))
    return Response(
        {"message": "Đăng sách thành công! Đang chờ admin duyệt.",
         "book": BookListSerializer(book).data},
        status=status.HTTP_201_CREATED,
    )


@api_view(['PATCH', 'DELETE'])
@permission_classes([AllowAny])
def book_manage(request, pk):
    """
    PATCH  /api/catalog/books/<pk>/manage/  — seller sửa sách của mình
    DELETE /api/catalog/books/<pk>/manage/  — seller xoá sách của mình
    """
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response({"error": "Không tìm thấy sách."}, status=status.HTTP_404_NOT_FOUND)

    user_id = getattr(request, 'user_id', None)
    roles   = getattr(request, 'user_roles', [])

    # Seller chỉ được sửa sách của shop mình; admin được tất cả
    is_admin = 'admin' in roles
    can_edit = is_admin or has_permission(request, 'catalog:book:update_own')

    if not can_edit:
        return Response({"error": "Không có quyền."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        book.is_active = False
        book.save(update_fields=['is_active'])
        return Response({"message": "Đã xoá sách."})

    serializer = BookUploadSerializer(
        book, data=request.data, partial=True,
        context={'request_user_id': user_id or 0}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(BookDetailSerializer(book).data)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ══════════════════════════════════════════════════════════════════════════════
# BOOK — admin publish
# ══════════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def book_publish(request, pk):
    """POST /api/catalog/books/<pk>/publish/ — admin duyệt sách"""
    if not has_permission(request, 'catalog:book:publish'):
        return require_permission_response('catalog:book:publish')
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response({"error": "Không tìm thấy sách."}, status=status.HTTP_404_NOT_FOUND)

    book.is_active = True
    book.save(update_fields=['is_active'])
    return Response({"message": f"Đã duyệt sách '{book.title}'."})


# ── Health ────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "service": "catalog_service"})
