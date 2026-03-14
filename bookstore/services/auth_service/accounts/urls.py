from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path('register/',         views.RegisterView.as_view(),   name='register'),
    path('login/',            views.LoginView.as_view(),      name='login'),
    path('logout/',           views.logout_view,              name='logout'),
    path('token/refresh/',    TokenRefreshView.as_view(),     name='token-refresh'),

    # ── Profile ───────────────────────────────────────────
    path('profile/',          views.ProfileView.as_view(),    name='profile'),
    path('change-password/',  views.change_password,          name='change-password'),

    # ── Seller / Author profiles ──────────────────────────
    path('seller-profile/',   views.SellerProfileView.as_view(),  name='seller-profile'),
    path('author-profile/',   views.AuthorProfileView.as_view(),  name='author-profile'),

    # ── Role management (admin) ───────────────────────────
    path('roles/assign/',     views.assign_role,   name='role-assign'),
    path('roles/revoke/',     views.revoke_role,   name='role-revoke'),

    # ── Utils ─────────────────────────────────────────────
    path('verify/',           views.verify_token,  name='verify'),
    path('health/',           views.health_check,  name='health'),
]
