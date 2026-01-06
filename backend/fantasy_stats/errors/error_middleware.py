import re
import json
import traceback
import threading
import time
from django.http import JsonResponse, HttpRequest, HttpResponseNotFound
from django.utils.deprecation import MiddlewareMixin

from .email import send_error_email
from .error_codes import InvalidLeagueError, JsonErrorCodes

# Shared state for batching
_error_buffer = []
_buffer_lock = threading.Lock()
_timer_running = False
BATCH_DELAY = 10  # seconds


def flush_errors():
    """
    Background worker: waits, then sends all buffered errors in one email.
    """
    global _timer_running
    time.sleep(BATCH_DELAY)

    with _buffer_lock:
        errors = list(_error_buffer)
        _error_buffer.clear()
        _timer_running = False

    if errors:
        try:
            combined = "\n\n---\n\n".join(errors)
            send_error_email(None, combined, is_exception=True)
        except Exception as e:
            print(f"Failed to send batched error email: {e}")


class SecurityAlertMiddleware(MiddlewareMixin):
    """
    Detects obvious automated attack probes.
    Sends a security alert email and immediately stops further processing.
    Returns a 404 so Django does NOT throw its own CSRF/403 errors.
    """

    SUSPICIOUS_PATHS = [
        r"\.php$",
        r"wp-admin",
        r"wp-json",
        r"xmlrpc\.php",
        r"vendor/.*/profile\.php",
        r"admin-ajax\.php",
        r"phpmyadmin",
    ]

    SUSPICIOUS_PAYLOAD = [
        r"select.+from",
        r"base64",
        r"convert_from",
        r"shell",
        r"cmd",
    ]

    def process_request(self, request: HttpRequest):
        path = request.path.lower()

        # ---- Check suspicious URLs ----
        for pattern in self.SUSPICIOUS_PATHS:
            if re.search(pattern, path):
                self._trigger_alert(request, reason=f"path matched: {pattern}")
                return self._block_response()  # ← STOP PIPELINE HERE

        # ---- Check suspicious POST bodies ----
        if request.method == "POST":
            raw_body = request.body.decode(errors="ignore").lower()

            for pattern in self.SUSPICIOUS_PAYLOAD:
                if re.search(pattern, raw_body):
                    self._trigger_alert(request, reason=f"payload matched: {pattern}")
                    return self._block_response()  # ← STOP PIPELINE HERE

        return None  # normal traffic continues

    # --------------------------------------------------------------
    #  ALERT + STOP EXECUTION
    # --------------------------------------------------------------
    def _trigger_alert(self, request: HttpRequest, reason: str):
        try:
            send_error_email(
                "Someone tried to attack you!\nReason: " + reason,
                request,
                is_exception=False,
            )
        except Exception:
            pass  # never break the site

    def _block_response(self):
        """
        Return a generic 404 and DO NOT let Django process further.
        Prevents duplicate emails from downstream CSRF/403 handlers.
        """
        return HttpResponseNotFound("<h1>404 Not Found</h1>")


class ErrorStatusEmailMiddleware(MiddlewareMixin):
    ERROR_STATUSES = [400, 401, 403, 404, 500]

    def process_exception(self, request, exception):
        """
        Called if a view raises an exception.
        """
        # Some errors should be skipped
        if isinstance(exception, InvalidLeagueError):
            print("InvalidLeagueError, skipping email.")
            return JsonResponse({"error": str(exception)}, status=400)

        error_messages_to_skip = [
            "LeagueInfo matching query does not exist",
            "An existing league is now invalid",
            "not found. Please check that you have entered the correct league ID and year.",
        ]
        if any(msg in str(exception) for msg in error_messages_to_skip):
            print("Known error occurred, skipping email.")
            return JsonResponse({"error": str(exception)}, status=400)

        if (
            hasattr(exception, "code")
            and exception.code == JsonErrorCodes.LEAGUE_SIGNUP_FAILURE.value
        ):
            print("LEAGUE_SIGNUP_FAILURE, skipping email.")
            return JsonResponse({"error": str(exception)}, status=400)

        # These errors will trigger an email
        error_text = f"""
        Exception at {request.build_absolute_uri()}:
        {traceback.format_exc()}
        """
        print(error_text)
        self._add_to_buffer(error_text)

        return JsonResponse(
            {"error": "An unexpected server error occurred."},
            status=500,
        )

    def process_response(self, request, response):
        """
        Called after a view returns a response.
        """
        if response.status_code in self.ERROR_STATUSES:
            try:
                error_message = None
                if hasattr(response, "content") and "application/json" in response.get(
                    "Content-Type", ""
                ):
                    try:
                        error_message = json.loads(
                            response.content.decode("utf-8")
                        ).get("error", "No message")
                    except Exception:
                        error_message = response.content.decode("utf-8")
                else:
                    error_message = response.content.decode("utf-8")

                msg = f"""
                Error {response.status_code} at {request.build_absolute_uri()}
                User URL: {request.META.get("HTTP_REFERER", "N/A")}
                Method: {request.method}
                GET params: {request.GET.dict()}
                POST data: {request.POST.dict()}

                Error message: {error_message}
                """
                print(msg)

                # Skip known error messages (same as process_exception)
                error_messages_to_skip = [
                    "LeagueInfo matching query does not exist",
                    "An existing league is now invalid",
                    "not found. Please check that you have entered the correct league ID and year.",
                ]
                if any(msg in error_message for msg in error_messages_to_skip):
                    print("Known error occurred in response, skipping email.")
                    return response

                self._add_to_buffer(msg)

            except Exception as e:
                print(f"Failed to buffer error: {e}")

        return response

    def _add_to_buffer(self, error_text):
        """
        Add error to the buffer and start a background flush timer if needed.
        """
        global _timer_running
        with _buffer_lock:
            _error_buffer.append(error_text.strip())
            if not _timer_running:
                _timer_running = True
                threading.Thread(target=flush_errors, daemon=True).start()


class LeagueErrorMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        return JsonResponse(
            {
                "status": "error",
                "code": JsonErrorCodes.LEAGUE_SIGNUP_FAILURE.value,
                "error": str(exception),
            },
            status=400,
        )
