from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailBackend(ModelBackend):
    """
    Authenticate with email + password instead of username + password.

    Falls back to Django's default ModelBackend if authentication fails,
    so playoff_pool's username-based login continues to work.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # Accept both authenticate(email=...) and authenticate(username=...) call styles.
        email = kwargs.get("email") or username
        if not email or not password:
            return None

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Run the hasher anyway to prevent timing attacks.
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
