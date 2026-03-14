from django.urls import path
from pages import views

urlpatterns = [
    path('',                    views.home,          name='home'),
    path('catalogue/',          views.catalogue,     name='catalogue'),
    path('books/<slug:slug>/',  views.book_detail,   name='book-detail'),
    path('seller/upload/',      views.book_upload,   name='book-upload'),
    path('register/',           views.register,      name='register'),
    path('login/',              views.login,         name='login'),
    path('logout/',             views.logout,        name='logout'),
    path('profile/',            views.profile,       name='profile'),
]
