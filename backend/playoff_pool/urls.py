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
)

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
    # API routes
    path("api/", include(router.urls)),
]
