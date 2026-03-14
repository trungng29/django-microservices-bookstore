"""
Permission decorators cho các microservice views.
Đặt file này vào mỗi service (hoặc dùng chung qua shared package).

Usage:
    from shared.decorators import require_permission, require_role

    @require_permission('catalog:book:create')
    def create_book(request): ...

    @require_role('seller', 'admin')
    def seller_dashboard(request): ...
"""
from functools import wraps
from rest_framework.response import Response
from rest_framework import status


def require_auth(func):
    """Yêu cầu đăng nhập."""
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if not getattr(request, 'is_authenticated', False):
            return Response(
                {"error": "Vui lòng đăng nhập.", "code": "not_authenticated"},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return func(request, *args, **kwargs)
    return wrapper


def require_role(*role_names):
    """Yêu cầu user có ít nhất 1 trong các role cho trước."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not getattr(request, 'is_authenticated', False):
                return Response(
                    {"error": "Vui lòng đăng nhập.", "code": "not_authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user_roles = getattr(request, 'user_roles', [])
            if not any(r in user_roles for r in role_names):
                return Response(
                    {
                        "error": f"Cần có role: {', '.join(role_names)}.",
                        "code":  "forbidden",
                        "your_roles": user_roles,
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_permission(*codenames):
    """Yêu cầu user có ít nhất 1 trong các permission cho trước."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not getattr(request, 'is_authenticated', False):
                return Response(
                    {"error": "Vui lòng đăng nhập.", "code": "not_authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user_perms = getattr(request, 'user_permissions', [])
            if not any(p in user_perms for p in codenames):
                return Response(
                    {
                        "error": f"Không có quyền thực hiện.",
                        "code":  "forbidden",
                        "required_one_of": list(codenames),
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_all_permissions(*codenames):
    """Yêu cầu user có TẤT CẢ các permission cho trước."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not getattr(request, 'is_authenticated', False):
                return Response(
                    {"error": "Vui lòng đăng nhập.", "code": "not_authenticated"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user_perms = set(getattr(request, 'user_permissions', []))
            missing = [p for p in codenames if p not in user_perms]
            if missing:
                return Response(
                    {
                        "error": "Không đủ quyền.",
                        "code":  "forbidden",
                        "missing_permissions": missing,
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
