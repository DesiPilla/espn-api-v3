from functools import wraps

from django.http import JsonResponse
from rest_framework.authtoken.models import Token


def token_auth_required(view_func):
    """
    Decorator for plain Django views that enforces DRF token authentication.

    Reads the Authorization: Token <key> header, validates it, and sets
    request.user before calling the wrapped view. Returns 401 JSON if the
    header is missing or the token is invalid.

    CSRF is marked exempt because token auth uses the Authorization header, not
    cookies, so it is not susceptible to CSRF attacks.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Token "):
            return JsonResponse({"error": "Authentication required."}, status=401)
        token_key = auth_header.split(" ", 1)[1].strip()
        try:
            token = Token.objects.select_related("user").get(key=token_key)
        except Token.DoesNotExist:
            return JsonResponse({"error": "Invalid or expired token."}, status=401)
        request.user = token.user
        return view_func(request, *args, **kwargs)

    wrapper.csrf_exempt = True
    return wrapper
