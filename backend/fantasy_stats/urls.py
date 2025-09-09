# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 20:38:57 2021

@author: desid
"""

from django.urls import path, re_path

from . import views

app_name = "fantasy_stats"

urlpatterns = [
    # Backend URLs for React
    path("api/leagues/", views.leagues_data, name="leagues_data"),
    path("api/league/<int:year>/<int:league_id>/", views.get_league_details),
    path("api/distinct-leagues-previous/", views.get_distinct_leagues_previous_year),
    path("api/copy-old-league/<int:league_id>/", views.copy_old_league),
    path("api/league-input/", views.league_input),
    path(
        "api/box-scores/<int:league_year>/<int:league_id>/<int:week>/",
        views.box_scores_view,
    ),
    path(
        "api/league/<int:league_year>/<int:league_id>/current-week/",
        views.get_current_week,
    ),
    path(
        "api/weekly-awards/<int:league_year>/<int:league_id>/<int:week>/",
        views.weekly_awards_view,
        name="weekly-awards",
    ),
    path(
        "api/power-rankings/<int:league_year>/<int:league_id>/<int:week>/",
        views.power_rankings_view,
        name="power-rankings",
    ),
    path(
        "api/luck-index/<int:league_year>/<int:league_id>/<int:week>/",
        views.luck_index_view,
        name="luck-index",
    ),
    path(
        "api/naughty-list/<int:league_year>/<int:league_id>/<int:week>/",
        views.naughty_list_view,
        name="naughty-list",
    ),
    path(
        "api/standings/<int:league_year>/<int:league_id>/<int:week>/",
        views.standings_view,
        name="standings",
    ),
    path(
        "api/simulate-playoff-odds/<int:league_year>/<int:league_id>/",
        views.simulate_playoff_odds_view,
        name="simulate-playoff-odds",
    ),
    path(
        "api/remaining-strength-of-schedule/<int:league_year>/<int:league_id>/",
        views.remaining_strength_of_schedule_view,
        name="remaining-strength-of-schedule",
    ),
    path(
        "api/season-records/<int:league_year>/<int:league_id>/",
        views.season_records,
        name="season-records",
    ),
    path(
        "api/check-league-status/<int:league_year>/<int:league_id>/",
        views.check_league_status,
        name="check_league_status",
    ),
    path(
        "api/league-settings/<int:league_year>/<int:league_id>/",
        views.league_settings,
        name="league-settings",
    ),
    path("api/test-error-email/", views.test_error_email, name="test_error_email"),
    path(
        "api/test-uh-oh-too-soon-error/",
        views.test_uh_oh_too_soon_error,
        name="test_uh_oh_too_soon_error",
    ),
    path(
        "api/test-invalid-league-error/",
        views.test_invalid_league_error,
        name="test_invalid_league_error",
    ),
    # Add this last, after all other routes
    path("api/get-csrf-token/", views.get_csrf_token, name="get_csrf_token"),
    # Catch-all: serve React index.html for any path
    re_path("", views.ReactAppView.as_view(), name="react-app"),
    re_path(r"^(?:.*)/?$", views.ReactAppView.as_view(), name="react-app"),
]
