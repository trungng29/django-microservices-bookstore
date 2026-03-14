from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserRole, Role, Permission, RolePermission, SellerProfile, AuthorProfile, LoginAttempt


class UserRoleInline(admin.TabularInline):
    model  = UserRole
    extra  = 1
    fields = ['role', 'assigned_at', 'expires_at']
    readonly_fields = ['assigned_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display    = ('id', 'email', 'username', 'primary_role_display', 'is_active', 'is_verified', 'date_joined')
    list_filter     = ('is_active', 'is_staff', 'is_verified', 'user_roles__role__name')
    search_fields   = ('email', 'username')
    ordering        = ('-date_joined',)
    readonly_fields = ('id', 'date_joined', 'last_login', 'updated_at')
    inlines         = [UserRoleInline]

    fieldsets = (
        (None,            {'fields': ('id', 'email', 'password')}),
        ('Personal info', {'fields': ('username', 'first_name', 'last_name', 'phone', 'bio', 'avatar')}),
        ('Status',        {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')}),
        ('Dates',         {'fields': ('date_joined', 'last_login', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('email', 'username', 'password1', 'password2')}),
    )

    def primary_role_display(self, obj):
        return obj.primary_role
    primary_role_display.short_description = 'Role'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ('name', 'display_name', 'permission_count', 'is_active')
    search_fields = ('name',)

    def permission_count(self, obj):
        return obj.role_permissions.count()
    permission_count.short_description = 'Permissions'


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ('codename', 'service', 'resource', 'action')
    list_filter   = ('service', 'resource')
    search_fields = ('codename', 'name')


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'business_name', 'verify_status', 'commission_rate')
    list_filter   = ('verify_status',)
    search_fields = ('user__username', 'user__email', 'business_name')


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'pen_name', 'is_verified', 'royalty_rate')
    list_filter   = ('is_verified',)
    search_fields = ('user__username', 'pen_name')


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display    = ('email', 'ip_address', 'success', 'timestamp')
    list_filter     = ('success',)
    readonly_fields = ('email', 'ip_address', 'success', 'timestamp', 'user_agent')
