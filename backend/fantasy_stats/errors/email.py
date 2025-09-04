import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd
from django.http import JsonResponse

from backend.src.doritostats.fetch_utils import get_postgres_conn
from backend.fantasy_stats.models import LeagueInfo


def send_new_league_added_alert(league_info: LeagueInfo):
    print("Sending email notification...")
    try:
        # Load environment variables
        port = os.getenv("EMAIL_PORT")
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        print("Using email configs:")
        print(f"  port={port}")
        print(f"  sender_email={sender_email}")
        print(f"  sender_password={sender_password}")

        # Turn these into plain/html MIMEText objects
        league_name = league_info.league_name
        league_id = league_info.league_id
        year = league_info.league_year

        # Get the number of new leagues added
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
        email_template = f"""
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
        email_body = MIMEText(email_template, "html")

        # Create a secure SSL context
        context = ssl.create_default_context()

        # Create the email message
        message = MIMEMultipart("alternative")
        message["From"] = sender_email
        message["To"] = sender_email

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        # message.attach(part1)
        message.attach(email_body)
        message["Subject"] = "New League Added: {} ({})".format(league_name, year)

        # Create secure connection with server and send email
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, sender_email, message.as_string())

    except Exception as e:
        # Fail silently but log
        print(f"Failed to send error email: {e}")

    finally:
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )
