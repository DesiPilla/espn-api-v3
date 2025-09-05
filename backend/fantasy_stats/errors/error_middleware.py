import json

from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

from .error_codes import JsonErrorCodes
from .email import send_error_email

# If you have certain codes you don't want to email on:
ERROR_MESSAGES_TO_SKIP_EMAIL = [
    JsonErrorCodes.TOO_SOON.value,
    JsonErrorCodes.LEAGUE_SIGNUP_FAILURE.value,
]


class ErrorStatusEmailMiddleware(MiddlewareMixin):
    """
    Middleware that emails on exceptions or error responses (>=400).
    """

    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        """
        response = JsonResponse(
            {"error": "An unexpected server error occurred."},
            status=500,
        )

        try:
            send_error_email(request, exception, is_exception=True)
        except Exception as email_exc:
            # Don't let email failures take down the app
            print(f"Failed to send error email (exception case): {email_exc}")

        return response

    def process_response(self, request, response):
        """
        Called after a view returns a response.
        """
        try:
            if hasattr(response, "status_code") and response.status_code >= 400:
                # Try to parse JSON to check for skip codes
                try:
                    data = json.loads(response.content)
                except Exception:
                    data = {}

                if data.get("code") in ERROR_MESSAGES_TO_SKIP_EMAIL:
                    print(
                        f"No need to send an email, this is just a '{data.get('code')}' error."
                    )
                else:
                    try:
                        send_error_email(request, response)
                    except Exception as email_exc:
                        print(
                            f"Failed to send error email (response case): {email_exc}"
                        )
        finally:
            return response
