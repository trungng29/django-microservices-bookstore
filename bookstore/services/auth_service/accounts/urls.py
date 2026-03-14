from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # ── Auth ───────────────────────────────────────────
    path('register/',        views.RegisterView.as_view(),   name='auth-register'),
    path('login/',           views.LoginView.as_view(),      name='auth-login'),
    path('logout/',          views.logout_view,              name='auth-logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),     name='token-refresh'),

    # ── Profile ────────────────────────────────────────
    path('profile/',         views.ProfileView.as_view(),    name='auth-profile'),
    path('change-password/', views.change_password,          name='auth-change-password'),

    # ── Utils ──────────────────────────────────────────
    path('verify/',          views.verify_token,             name='auth-verify'),
    path('health/',          views.health_check,             name='auth-health'),
]
