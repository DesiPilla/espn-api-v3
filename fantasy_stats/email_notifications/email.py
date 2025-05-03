import os
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import pandas as pd

from src.doritostats.fetch_utils import get_postgres_conn
from fantasy_stats.models import LeagueInfo


def send_new_league_added_alert(league_info: LeagueInfo):
    # Load environment variables
    port = os.getenv("EMAIL_PORT")
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASSWORD")

    # Read in the email template
    email_template_file = open(
        "fantasy_stats/email_notifications/new_league_added.txt", "r"
    )
    email_template = email_template_file.read()
    email_template_file.close()

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
    email_body = MIMEText(
        email_template.format(
            league_name,
            league_id,
            year,
            pd.Timestamp.now(tz="US/Eastern").strftime("%B %d, %Y @ %I:%M %p"),
            n_leagues_2025,
            n_leagues_added_this_year,
            n_leagues_added_all_time,
        ),
        "html",
    )

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
