try:
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import TokenError
except ImportError:
    AccessToken = None

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.user_id          = None
        request.user_roles       = []
        request.user_permissions = []
        request.primary_role     = None
        request.is_authenticated = False

        if AccessToken:
            auth = request.META.get('HTTP_AUTHORIZATION', '')
            if auth.startswith('Bearer '):
                try:
                    token = AccessToken(auth.split(' ', 1)[1])
                    request.user_id          = token.get('user_id')
                    request.user_roles       = token.get('roles', [])
                    request.user_permissions = token.get('permissions', [])
                    request.primary_role     = token.get('primary_role', 'customer')
                    request.is_authenticated = True
                except Exception:
                    pass

        return self.get_response(request)
