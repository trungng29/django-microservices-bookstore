"""
ServicePermissionMiddleware
Dùng cho các microservice (catalog, shop, order, interaction).
Đặt vào MIDDLEWARE của từng service để decode JWT và inject thông tin vào request.

Các service KHÔNG cần gọi lại auth_service mỗi request —
tất cả roles + permissions đã được nhét vào JWT payload khi login.
"""
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError


class JWTAuthMiddleware:
    """
    Decode JWT từ Authorization header và gắn vào request:
      request.user_id
      request.user_roles      → ['seller', 'author']
      request.user_permissions → ['catalog:book:create', ...]
      request.primary_role    → 'seller'
      request.is_authenticated → True/False
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id          = None
        request.user_roles       = []
        request.user_permissions = []
        request.primary_role     = None
        request.is_authenticated = False

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token_str = auth_header.split(' ', 1)[1]
            try:
                token = AccessToken(token_str)
                request.user_id          = token.get('user_id')
                request.user_roles       = token.get('roles', [])
                request.user_permissions = token.get('permissions', [])
                request.primary_role     = token.get('primary_role', 'customer')
                request.is_authenticated = True
            except TokenError:
                pass

        return self.get_response(request)
