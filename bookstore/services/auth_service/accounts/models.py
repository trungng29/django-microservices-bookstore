from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import re


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        if not username:
            raise ValueError('Username is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)   # ← bcrypt hash via Django
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model with auto-increment PK (BigAutoField via DEFAULT_AUTO_FIELD).
    Password is stored as Django's PBKDF2 hash (set_password / check_password).
    """
    # id is BigAutoField (auto-increment) from DEFAULT_AUTO_FIELD in settings
    email       = models.EmailField(unique=True, max_length=255)
    username    = models.CharField(unique=True, max_length=50)
    first_name  = models.CharField(max_length=50, blank=True)
    last_name   = models.CharField(max_length=50, blank=True)
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio         = models.TextField(blank=True, max_length=500)
    phone       = models.CharField(max_length=15, blank=True)

    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)  # email verification

    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.username} <{self.email}>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username


class LoginAttempt(models.Model):
    """Track failed login attempts for rate limiting / security audit."""
    email      = models.EmailField()
    ip_address = models.GenericIPAddressField(null=True)
    success    = models.BooleanField(default=False)
    timestamp  = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = 'login_attempts'
        indexes = [models.Index(fields=['email', 'timestamp'])]
