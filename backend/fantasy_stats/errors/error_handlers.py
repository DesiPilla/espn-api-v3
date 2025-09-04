import json
import os
import traceback
from functools import wraps

import resend
from django.http import JsonResponse

from backend.fantasy_stats.errors.error_codes import JsonErrorCodes

ERROR_MESSAGES_TO_SKIP_EMAIL = [
    JsonErrorCodes.TOO_SOON.value,
    JsonErrorCodes.LEAGUE_SIGNUP_FAILURE.value,
]

def error_email_on_failure(view_func):
    """
    Decorator for Django views. If the view raises an exception or returns
    an error response (status 400+), an email is sent to the admin.
    """

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        try:
            response = view_func(request, *args, **kwargs)

            # Check if response is an error (for DRF Response or HttpResponse)
            if hasattr(response, "status_code") and response.status_code >= 400:
                data = json.loads(response.content)
                if data.get("code") in ERROR_MESSAGES_TO_SKIP_EMAIL:
                    print(
                        f"No need to send an email, this is just a '{data.get('code')}' error."
                    )
                else:
                    send_error_email(request, response)

        except Exception as exc:
            response = JsonResponse(
                {"error": "An unexpected server error occurred."},
                status=500,
            )

            # If the view raises an exception, send email with traceback
            send_error_email(request, exc, is_exception=True)

        finally:
            return response

    return _wrapped_view


def send_error_email(request, info, is_exception=False):
    """
    Sends an email with error details.
    """
    print("Sending email notification...")
    try:
        # Load environment variables
        sender_email = os.getenv("SENDER_EMAIL")
        recipient_email = os.getenv("RECIPIENT_EMAIL")
        resend.api_key = os.getenv("RESEND_API_KEY")
        print("Using email configs:")
        print(f"  sender_email={sender_email}")
        print(f"  recipient_email={recipient_email}")

        # Build message
        body = f"""
<html>
  <body>
    <h3>API Error Notification</h3>
    <pre>
HTTP Method: {request.method}
User URL: {request.META.get('HTTP_REFERER', 'N/A')}
API URL: {request.build_absolute_uri()}

GET params:
{json.dumps(request.GET.dict(), indent=4)}

POST data:
{json.dumps(request.POST.dict(), indent=4)}
    </pre>
"""

        if is_exception:
            body += f"""
            <b>Exception:</b>
            <pre>{str(info)}

        Traceback:
        {traceback.format_exc()}</pre>
            """
        else:
            # info is an HttpResponse
            try:
                if "application/json" in info.get("Content-Type", ""):
                    response_data = json.loads(info.content.decode("utf-8"))
                    body += f"""
            <b>Response Body:</b>
            <pre>{json.dumps(response_data, indent=4)}</pre>
                    """
                else:
                    body += f"""
            <b>Response Body:</b>
            <pre>{info.content.decode('utf-8')}</pre>
                    """
            except Exception:
                body += """
            <b>Response Body:</b>
            <pre>Unable to parse response content</pre>
                """

        body += """
        </body>
        </html>
        """

        response = resend.Emails.send(
            {
                "from": sender_email,
                "to": [recipient_email],
                "subject": f"[Django] Error Notification",
                "html": body,
            }
        )
        print(response)
        print("Email sent successfully.")

    except Exception as e:
        response = JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )

        # Fail silently but log
        print(f"Failed to send error email: {e}")

    finally:
        return response
