from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, LoginAttempt


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('id', 'email', 'username', 'full_name', 'is_active', 'is_verified', 'date_joined')
    list_filter   = ('is_active', 'is_staff', 'is_verified')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering      = ('-date_joined',)
    readonly_fields = ('id', 'date_joined', 'last_login', 'updated_at')

    fieldsets = (
        (None,            {'fields': ('id', 'email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone', 'bio', 'avatar')}),
        ('Permissions',   {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Dates',         {'fields': ('date_joined', 'last_login', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display  = ('email', 'ip_address', 'success', 'timestamp')
    list_filter   = ('success',)
    search_fields = ('email', 'ip_address')
    readonly_fields = ('email', 'ip_address', 'success', 'timestamp', 'user_agent')
