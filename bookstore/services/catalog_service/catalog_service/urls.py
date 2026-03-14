from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from books import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # ── Public ────────────────────────────────────────────
    path('api/catalog/books/',              views.BookListView.as_view(),      name='book-list'),
    path('api/catalog/books/<slug:slug>/',  views.book_detail,                 name='book-detail'),
    path('api/catalog/authors/',            views.AuthorListCreateView.as_view(), name='author-list'),
    path('api/catalog/authors/<int:pk>/',   views.AuthorDetailView.as_view(),  name='author-detail'),
    path('api/catalog/publishers/',         views.PublisherListCreateView.as_view(), name='publisher-list'),
    path('api/catalog/categories/',         views.category_list,               name='category-list'),
    # ── Seller ────────────────────────────────────────────
    path('api/catalog/books/upload/',       views.book_upload,                 name='book-upload'),
    path('api/catalog/books/<int:pk>/manage/', views.book_manage,              name='book-manage'),
    # ── Admin ─────────────────────────────────────────────
    path('api/catalog/books/<int:pk>/publish/', views.book_publish,            name='book-publish'),
    # ── Health ────────────────────────────────────────────
    path('api/catalog/health/',             views.health_check,                name='health'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
