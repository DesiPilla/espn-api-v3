# backend/fantasy_stats/middleware.py
import os
import smtplib, ssl
import traceback
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.utils.deprecation import MiddlewareMixin


class ErrorEmailMiddleware(MiddlewareMixin):
    ERROR_STATUSES = [400, 401, 403, 404, 500]

    def process_response(self, request, response):
        if response.status_code in self.ERROR_STATUSES:
            try:
                # Extract error message
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

                # URLs
                user_url = request.META.get("HTTP_REFERER", "N/A")
                api_url = request.build_absolute_uri()

                # Build email
                port = int(os.getenv("EMAIL_PORT", "465"))
                sender_email = os.getenv("EMAIL_USER")
                sender_password = os.getenv("EMAIL_PASSWORD")

                subject = f"[Django] {response.status_code} Error at {request.path}"
                body = f"""
                HTTP Status: {response.status_code}

                User visited URL: {user_url}
                API endpoint URL: {api_url}
                Method: {request.method}
                GET params: {request.GET.dict()}
                POST data: {request.POST.dict()}

                Error message: {error_message}

                Traceback (if available):
                {traceback.format_exc()}
                """

                message = MIMEMultipart("alternative")
                message["From"] = sender_email
                message["To"] = sender_email
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain"))

                # Send email via Gmail SSL
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    "smtp.gmail.com", port, context=context
                ) as server:
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, sender_email, message.as_string())

            except Exception as e:
                print(f"Failed to send error email: {e}")

        return response
