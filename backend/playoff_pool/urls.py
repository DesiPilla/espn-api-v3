from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LeagueViewSet,
    LeagueMembershipViewSet,
    DraftedTeamViewSet,
    login_user,
    register_user,
    scoring_settings,
    debug_test,
    get_league_info,
    available_league_years,
)
from .nfl_utils import current_nfl_season_api

app_name = 'playoff_pool'

router = DefaultRouter()
router.register(r'leagues', LeagueViewSet, basename='league')
router.register(r'memberships', LeagueMembershipViewSet, basename='membership')
router.register(r'drafted-teams', DraftedTeamViewSet, basename='drafted-team')

urlpatterns = [
    # Debug endpoint
    path("debug/", debug_test, name="debug_test"),
    # Authentication endpoints
    path("auth/login/", login_user, name="api_login"),
    path("auth/register/", register_user, name="api_register"),
    # League info endpoint (public)
    path("league-info/<int:league_id>/", get_league_info, name="league_info"),
    # Settings endpoint
    path("scoring-settings/", scoring_settings, name="scoring_settings"),
    # NFL utilities
    path("nfl/current-season/", current_nfl_season_api, name="current_nfl_season"),
    path("available-years/", available_league_years, name="available_league_years"),
    # API routes
    path("api/", include(router.urls)),
]
