import json
import os
import traceback

import resend
import pandas as pd

from backend.src.doritostats.fetch_utils import get_postgres_conn
from backend.fantasy_stats.models import LeagueInfo


def send_new_league_added_alert(league_info: LeagueInfo):
    # Load environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    resend.api_key = os.getenv("RESEND_API_KEY")

    # Turn these into plain/html MIMEText objects
    league_name = league_info.league_name
    league_id = league_info.league_id
    year = league_info.league_year

    # Build message
    conn = get_postgres_conn()
    n_leagues_2025 = pd.read_sql(
        "SELECT COUNT(*) FROM public.fantasy_stats_leagueinfo WHERE league_year = 2025",
        conn,
    ).values[0][0]
    n_leagues_added_this_year = pd.read_sql(
        "SELECT COUNT(*) FROM public.fantasy_stats_leagueinfo WHERE created_date > '2025-03-15'",
        conn,
    ).values[0][0]
    n_leagues_added_all_time = pd.read_sql(
        "SELECT COUNT(*) FROM public.fantasy_stats_leagueinfo", conn
    ).values[0][0]

    # Fill in the placeholders in the email template
    body = f"""
<html>
<body>
    <p>🎉🎉 A new league was added! 🎉🎉<br>
        <br>
        League name: {league_name} ({league_id})<br>
        League year: {year}<br>
        Date added:  {pd.Timestamp.now(tz='US/Eastern').strftime('%B %d, %Y @ %I:%M %p')}<br>
        <br>
        Total 2025 season leagues added: {n_leagues_2025}<br>
        Total leagues added this year:   {n_leagues_added_this_year}<br>
        Total leagues added all time:    {n_leagues_added_all_time}
    </p>
</body>
</html>
    """

    try:
        print("Sending email notification...")
        response = resend.Emails.send(
            {
                "from": sender_email,
                "to": [recipient_email],
                "subject": "New League Added: {} ({})".format(league_name, year),
                "html": body,
            }
        )
        print(response)
        print("Email sent successfully.")

    except Exception as e:
        # Fail silently but log
        print(f"Failed to send error email: {e}")


def send_error_email(request, info, is_exception=False):
    """
    Sends an email with error details.
    """
    # Load environment variables
    sender_email = os.getenv("SENDER_EMAIL")
    recipient_email = os.getenv("RECIPIENT_EMAIL")
    resend.api_key = os.getenv("RESEND_API_KEY")

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

    try:
        print("Sending email notification...")
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

        # Fail silently but log
        print(f"Failed to send error email: {e}")
