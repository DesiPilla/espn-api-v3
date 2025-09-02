import json
import os
import smtplib
import ssl
import traceback
from functools import wraps

from django.http import JsonResponse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        port = int(os.getenv("EMAIL_PORT", "465"))

        # Build message
        subject = f"[Django] Error Notification"
        body = f"""
HTTP Method: {request.method}
User URL: {request.META.get('HTTP_REFERER', 'N/A')}
API URL: {request.build_absolute_uri()}
GET params: {json.dumps(request.GET.dict(), indent=4)}
POST data: {json.dumps(request.POST.dict(), indent=4)}
"""

        if is_exception:
            body += f"Exception: {str(info)}\n\nTraceback:\n{traceback.format_exc()}"
        else:
            # info is an HttpResponse
            try:
                if "application/json" in info.get("Content-Type", ""):
                    response_data = json.loads(info.content.decode("utf-8"))
                    body += f"Response Body: {json.dumps(response_data, indent=4)}\n\n"
                else:
                    body += f"Response Body: {info.content.decode('utf-8')}\n\n"
            except Exception:
                body += "Response Body: Unable to parse response content\n\n"

        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = sender_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Send email via SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, sender_email, message.as_string())
        print("Email sent successfully.")

    except Exception as e:
        # Fail silently but log
        print(f"Failed to send error email: {e}")

    finally:
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )
