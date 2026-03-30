from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime
import pandas as pd
import logging

from .models import (
    League,
    LeagueMembership,
    DraftedTeam,
    UserProfile,
    LeagueScoringSetting,
    PlayoffDraftablePlayer,
)
from backend.playoff_pool.players import query_playoff_players_from_db
from backend.playoff_pool.scoring import (
    SCORING_MULTIPLIERS,
    DEFENSE_SCORING_MULTIPLIERS,
)

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@permission_classes([permissions.AllowAny])
def debug_test(request):
    """Debug endpoint to test routing"""
    logger.info(f"DEBUG_TEST: Received {request.method} request")
    return Response(
        {
            "message": f"Debug endpoint reached with {request.method} method",
            "path": request.path,
            "method": request.method,
        }
    )


from .serializers import (
    LeagueSerializer,
    LeagueMembershipSerializer,
    DraftedTeamSerializer,
    UserRegistrationSerializer,
    UserSerializer,
    DraftPlayerSerializer,
    AvailablePlayerSerializer,
    LeagueScoringSettingSerializer,
)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """Login user and return auth token"""
    logger.info(f"LOGIN_USER: Received {request.method} request to login_user")
    logger.info(f"LOGIN_USER: Request data: {request.data}")
    logger.info(f"LOGIN_USER: Request headers: {dict(request.headers)}")

    username = request.data.get("username")
    password = request.data.get("password")

    logger.info(
        f"LOGIN_USER: Username: {username}, Password length: {len(password) if password else 0}"
    )

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        # Get or create user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": profile.display_name,
                },
            }
        )
    else:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_user(request):
    """Register a new user"""
    logger.info(f"REGISTER_USER: Received {request.method} request to register_user")
    logger.info(f"REGISTER_USER: Request data: {request.data}")
    logger.info(f"REGISTER_USER: Request headers: {dict(request.headers)}")

    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        profile = UserProfile.objects.get(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": profile.display_name,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def get_league_info(request, league_id):
    """Get basic league info without authentication (for join links)"""
    try:
        league = League.objects.get(id=league_id)
        members = LeagueMembership.objects.filter(league=league)

        # Get unclaimed teams count
        unclaimed_teams = members.filter(user=None).count()
        claimed_teams = members.filter(user__isnull=False).count()

        return Response(
            {
                "id": league.id,
                "name": league.name,
                "created_by": league.created_by.username if league.created_by else None,
                "num_teams": league.num_teams,
                "claimed_teams": claimed_teams,
                "unclaimed_teams": unclaimed_teams,
                "available_spots": league.num_teams - members.count(),
                "is_draft_complete": league.is_draft_complete,
                "unclaimed_team_list": [
                    {
                        "id": team.id,
                        "team_name": team.team_name,
                        "joined_at": team.joined_at,
                    }
                    for team in members.filter(user=None)
                ],
            }
        )
    except League.DoesNotExist:
        return Response({"error": "League not found"}, status=status.HTTP_404_NOT_FOUND)


@ensure_csrf_cookie
@api_view(["GET"])
def scoring_settings(request):
    """Get default scoring settings with categories"""

    def categorize_stats(stats_dict, is_defensive=False):
        """
        Simplified categorization - now just extracts info from the stat config dict
        """
        categorized = {}
        for stat, config in stats_dict.items():
            # Extract category and display_name from config
            category = config["category"]

            if category not in categorized:
                categorized[category] = []

            categorized[category].append(
                {
                    "stat_name": stat,
                    "display_name": config["display_name"],
                    "default_value": config["default_value"],
                    "increment_value": config["increment_value"],
                    "is_defensive_stat": is_defensive,
                }
            )

        return categorized

    offensive_stats = categorize_stats(SCORING_MULTIPLIERS, False)
    defensive_stats = categorize_stats(DEFENSE_SCORING_MULTIPLIERS, True)

    # Merge the dictionaries
    all_stats = {**offensive_stats, **defensive_stats}

    # Define category order and return ordered dictionary
    category_order = [
        "Passing",
        "Rushing",
        "Receiving",
        "Defense/Special Teams",
        "Kicking",
        "Returns",
        "Miscellaneous",
    ]

    # Create ordered categorized settings
    ordered_stats = {}
    for category in category_order:
        if category in all_stats:
            ordered_stats[category] = all_stats[category]

    return Response(
        {
            "scoring_categories": ordered_stats,
            "position_choices": [
                {"value": "QB", "label": "Quarterback"},
                {"value": "RB", "label": "Running Back"},
                {"value": "WR", "label": "Wide Receiver"},
                {"value": "TE", "label": "Tight End"},
                {"value": "K", "label": "Kicker"},
                {"value": "DST", "label": "Defense/Special Teams"},
            ],
        }
    )


class LeagueViewSet(viewsets.ModelViewSet):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]

    def dispatch(self, request, *args, **kwargs):
        """Add debugging for authentication"""
        logger.info(f"LEAGUE_VIEWSET: {request.method} request to {request.path}")
        logger.info(f"LEAGUE_VIEWSET: Headers: {dict(request.headers)}")
        logger.info(f"LEAGUE_VIEWSET: User: {request.user}")
        logger.info(
            f"LEAGUE_VIEWSET: User authenticated: {request.user.is_authenticated}"
        )
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # For list view, only return leagues the user is a member of
        if self.action == "list":
            return League.objects.filter(members__user=self.request.user).distinct()
        # For other actions (join, retrieve), allow access to all leagues
        return League.objects.all()

    def perform_create(self, serializer):
        # Create league with current user as creator
        league = serializer.save(created_by=self.request.user)

        # Add creator as admin member
        LeagueMembership.objects.create(
            user=self.request.user,
            league=league,
            team_name=f"{self.request.user.username}'s Team",
            is_admin=True,
        )

        # Handle custom scoring settings if provided, otherwise use defaults
        custom_scoring = self.request.data.get("scoring_settings", {})
        if custom_scoring:
            self._create_custom_scoring_settings(league, custom_scoring)
        else:
            self._create_default_scoring_settings(league)

    def _create_custom_scoring_settings(self, league, custom_scoring):
        """Create custom scoring settings for a new league"""
        # Get all available stats from defaults
        all_stats = {**SCORING_MULTIPLIERS, **DEFENSE_SCORING_MULTIPLIERS}

        # Create settings for all available stats
        for stat_name, config in all_stats.items():
            # Use custom value if provided, otherwise use default
            multiplier = custom_scoring.get(stat_name, config["default_value"])
            is_defensive = stat_name in DEFENSE_SCORING_MULTIPLIERS

            LeagueScoringSetting.objects.create(
                league=league,
                stat_name=stat_name,
                multiplier=multiplier,
                is_defensive_stat=is_defensive,
                category=config["category"],
                display_name=config["display_name"],
            )

    def _create_default_scoring_settings(self, league):
        """Create default scoring settings for a new league"""
        # Create offensive scoring settings for ALL stats (including zeros)
        for stat_name, config in SCORING_MULTIPLIERS.items():
            if stat_name:  # Only check that stat_name exists
                LeagueScoringSetting.objects.create(
                    league=league,
                    stat_name=stat_name,
                    multiplier=config["default_value"],
                    is_defensive_stat=False,
                    category=config["category"],
                    display_name=config["display_name"],
                )

        # Create defensive scoring settings for ALL stats (including zeros)
        for stat_name, config in DEFENSE_SCORING_MULTIPLIERS.items():
            if stat_name:  # Only check that stat_name exists
                LeagueScoringSetting.objects.create(
                    league=league,
                    stat_name=stat_name,
                    multiplier=config["default_value"],
                    is_defensive_stat=True,
                    category=config["category"],
                    display_name=config["display_name"],
                )

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        """Join a league"""
        league = self.get_object()
        team_name = request.data.get("team_name", f"{request.user.username}'s Team")
        confirm_multiple = request.data.get("confirm_multiple", False)

        # Check how many teams the user already has in this league
        existing_teams = LeagueMembership.objects.filter(
            user=request.user, league=league
        ).count()

        # If user already has teams but hasn't confirmed, return info for confirmation
        if existing_teams > 0 and not confirm_multiple:
            ordinal = {1: "second", 2: "third", 3: "fourth", 4: "fifth"}.get(
                existing_teams, f"{existing_teams + 1}th"
            )

            return Response(
                {
                    "requires_confirmation": True,
                    "existing_teams": existing_teams,
                    "ordinal": ordinal,
                    "message": f"You are already a member of this league. Are you sure you want to create a {ordinal} team?",
                },
                status=status.HTTP_200_OK,
            )

        # Check if league is full
        current_members = LeagueMembership.objects.filter(league=league).count()
        if current_members >= league.num_teams:
            return Response(
                {"error": "This league is full"}, status=status.HTTP_400_BAD_REQUEST
            )

        membership = LeagueMembership.objects.create(
            user=request.user, league=league, team_name=team_name
        )

        return Response(
            LeagueMembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def create_team(self, request, pk=None):
        """Create an unclaimed team (admin only)"""
        league = self.get_object()

        # Check if user is admin
        user_membership = LeagueMembership.objects.filter(
            user=request.user, league=league
        ).first()
        if not user_membership or not user_membership.is_admin:
            return Response(
                {"error": "Only league administrators can create teams"},
                status=status.HTTP_403_FORBIDDEN,
            )

        team_name = request.data.get("team_name")
        if not team_name:
            return Response(
                {"error": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if league is full
        current_members = LeagueMembership.objects.filter(league=league).count()
        if current_members >= league.num_teams:
            return Response(
                {"error": "This league is full"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create unclaimed team
        membership = LeagueMembership.objects.create(
            user=None,  # Unclaimed team
            league=league,
            team_name=team_name,
            is_admin=False,
        )

        return Response(
            LeagueMembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def claim_team(self, request, pk=None):
        """Claim an unclaimed team"""
        league = self.get_object()
        team_id = request.data.get("team_id")
        confirm_multiple = request.data.get("confirm_multiple", False)

        if not team_id:
            return Response(
                {"error": "Team ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Find unclaimed team
        try:
            team = LeagueMembership.objects.get(id=team_id, league=league, user=None)
        except LeagueMembership.DoesNotExist:
            return Response(
                {"error": "Team not found or already claimed"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check how many teams the user already has in this league
        existing_teams = LeagueMembership.objects.filter(
            user=request.user, league=league
        ).count()

        # If user already has teams but hasn't confirmed, return info for confirmation
        if existing_teams > 0 and not confirm_multiple:
            ordinal = {1: "second", 2: "third", 3: "fourth", 4: "fifth"}.get(
                existing_teams, f"{existing_teams + 1}th"
            )

            return Response(
                {
                    "requires_confirmation": True,
                    "existing_teams": existing_teams,
                    "ordinal": ordinal,
                    "team_name": team.team_name,
                    "message": f"You are already a member of this league. Are you sure you want to claim a {ordinal} team?",
                },
                status=status.HTTP_200_OK,
            )

        # Claim the team
        team.user = request.user
        team.save()

        # Update all DraftedTeam records for this team to link to this membership and user
        DraftedTeam.objects.filter(league=league, team_name=team.team_name).update(
            team_membership=team, user=request.user
        )

        # Note: Cache now stored in PostgreSQL, will auto-refresh on next view
        # No need to manually clear Django cache

        return Response(
            LeagueMembershipSerializer(team).data, status=status.HTTP_200_OK
        )

    @action(
        detail=True, methods=["delete", "patch"], url_path="teams/(?P<team_id>[^/.]+)"
    )
    def manage_team(self, request, pk=None, team_id=None):
        """Remove or update a team - DELETE to remove, PATCH to update team details"""
        if request.method == "DELETE":
            return self._remove_team(request, pk, team_id)
        elif request.method == "PATCH":
            return self._update_team(request, pk, team_id)

    def _remove_team(self, request, pk=None, team_id=None):
        """Remove a team from the league (admin only)"""
        league = self.get_object()

        # Check if user is admin
        user_membership = LeagueMembership.objects.filter(
            user=request.user, league=league, is_admin=True
        ).first()
        if not user_membership:
            return Response(
                {"error": "Only league administrators can remove teams"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            team = LeagueMembership.objects.get(id=team_id, league=league)
        except LeagueMembership.DoesNotExist:
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )

        team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _update_team(self, request, pk=None, team_id=None):
        """Update team details (name, etc.) - user can update their own team or admin can update any"""
        league = self.get_object()

        if not team_id:
            return Response(
                {"error": "Team ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = LeagueMembership.objects.get(id=team_id, league=league)
        except LeagueMembership.DoesNotExist:
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user owns this team or is an admin
        user_membership = LeagueMembership.objects.filter(
            user=request.user, league=league, is_admin=True
        ).first()

        if team.user != request.user and not user_membership:
            return Response(
                {"error": "You can only update your own team or you must be an admin"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Get the new team name from request data
        new_team_name = request.data.get("team_name", "").strip()

        if not new_team_name:
            return Response(
                {"error": "Team name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        if len(new_team_name) > 100:  # Assuming reasonable max length
            return Response(
                {"error": "Team name must be 100 characters or less"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if team name is already taken in this league
        existing_team = (
            LeagueMembership.objects.filter(league=league, team_name=new_team_name)
            .exclude(id=team.id)
            .first()
        )

        if existing_team:
            return Response(
                {"error": "Team name is already taken in this league"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_team_name = team.team_name
        team.team_name = new_team_name
        team.save()

        return Response(
            {
                "message": f"Team name updated from '{old_team_name}' to '{new_team_name}'",
                "team_name": new_team_name,
                "success": True,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def unclaim_team(self, request, pk=None):
        """Unclaim a team (make it available for others to claim)"""
        league = self.get_object()
        team_id = request.data.get("team_id")

        if not team_id:
            return Response(
                {"error": "Team ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            team = LeagueMembership.objects.get(id=team_id, league=league)
        except LeagueMembership.DoesNotExist:
            return Response(
                {"error": "Team not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if the user owns this team or is an admin
        user_membership = LeagueMembership.objects.filter(
            user=request.user, league=league, is_admin=True
        ).first()

        if team.user != request.user and not user_membership:
            return Response(
                {
                    "error": "You can only unclaim your own teams or you must be an admin"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Unclaim the team
        team.user = None
        team.save()

        return Response(
            {
                "message": f"Team '{team.team_name}' has been unclaimed and is now available"
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def members(self, request, pk=None):
        """Get league members"""
        league = self.get_object()
        members = LeagueMembership.objects.filter(league=league).select_related("user")
        serializer = LeagueMembershipSerializer(members, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def available_players(self, request, pk=None):
        """Get available players for drafting"""
        league = self.get_object()

        try:
            nfl_year = (
                league.league_year
                if hasattr(league, "league_year") and league.league_year
                else 2025
            )
            positions = (
                league.positions_included
                if league.positions_included
                else ["QB", "RB", "WR", "TE", "K", "DST"]
            )

            # Add flex eligible positions if flex is configured
            if league.roster_config and "flex" in league.roster_config:
                flex_config = league.roster_config["flex"]
                if (
                    isinstance(flex_config, dict)
                    and "eligible_positions" in flex_config
                ):
                    flex_eligible = flex_config["eligible_positions"]
                    # Add flex eligible positions to the list if not already included
                    for pos in flex_eligible:
                        if pos not in positions:
                            positions.append(pos)

            all_players = query_playoff_players_from_db(
                year=nfl_year, positions_to_keep=positions
            )

            # Get list of already drafted player gsis_ids for this league
            drafted_gsis_ids = set(
                DraftedTeam.objects.filter(league=league).values_list(
                    "gsis_id", flat=True
                )
            )

            # Filter out already drafted players
            available_players = [
                player
                for player in all_players
                if player.get("gsis_id") not in drafted_gsis_ids
            ]

            # Map full_name to name for frontend compatibility
            for player in available_players:
                player["name"] = player.get("full_name", "")

        except Exception as e:
            logger.exception(
                "Error retrieving available players for league %s", league.id
            )
            return Response(
                {
                    "error": "An internal error occurred while fetching available players."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(available_players)

    @action(detail=True, methods=["post"])
    def draft_player(self, request, pk=None):
        """Draft a player to a team"""
        league = self.get_object()

        # Check if user is admin
        try:
            membership = LeagueMembership.objects.filter(
                user=request.user, league=league, is_admin=True
            ).first()
            if not membership:
                return Response(
                    {"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {"error": "You are not a member of this league"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if league.is_draft_complete:
            return Response(
                {"error": "Draft is already complete"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DraftPlayerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        gsis_id = serializer.validated_data["gsis_id"]
        team_id = serializer.validated_data.get("team_id")
        user_id = serializer.validated_data.get("user_id")

        # Handle both old format (user_id) and new format (team_id)
        if team_id:
            try:
                target_membership = LeagueMembership.objects.get(
                    id=team_id, league=league
                )
                # target_user can be None for unclaimed teams
                target_user = target_membership.user
            except LeagueMembership.DoesNotExist:
                return Response(
                    {"error": "Invalid team or team not in league"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif user_id:
            try:
                target_user = User.objects.get(id=user_id)
                # For backward compatibility, get the first team if user has multiple
                target_membership = LeagueMembership.objects.filter(
                    user=target_user, league=league
                ).first()
                if not target_membership:
                    return Response(
                        {"error": "User not in league"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            except User.DoesNotExist:
                return Response(
                    {"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(
                {"error": "Either team_id or user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if player is already drafted
        if DraftedTeam.objects.filter(league=league, gsis_id=gsis_id).exists():
            return Response(
                {"error": "Player already drafted"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get player info first to check position limits
        try:
            nfl_year = (
                league.league_year
                if hasattr(league, "league_year") and league.league_year
                else 2025
            )
            positions = (
                league.positions_included
                if league.positions_included
                else ["QB", "RB", "WR", "TE", "K", "DST"]
            )

            # Add flex eligible positions if flex is configured
            if league.roster_config and "flex" in league.roster_config:
                flex_config = league.roster_config["flex"]
                if (
                    isinstance(flex_config, dict)
                    and "eligible_positions" in flex_config
                ):
                    flex_eligible = flex_config["eligible_positions"]
                    # Add flex eligible positions to the list if not already included
                    for pos in flex_eligible:
                        if pos not in positions:
                            positions.append(pos)

            available_players = query_playoff_players_from_db(
                year=nfl_year, positions_to_keep=positions
            )
            player_row = None
            for player in available_players:
                if str(player.get("gsis_id", "")) == gsis_id:
                    player_row = player
                    break

            if player_row is None:
                return Response(
                    {"error": "Player not found"}, status=status.HTTP_400_BAD_REQUEST
                )

            player_position = player_row.get("position", "Unknown")

            # Validate roster limits before drafting
            if league.roster_config and target_membership:
                error_message = self._validate_roster_limits(
                    league, target_membership, player_position
                )
                if error_message:
                    return Response(
                        {"error": error_message}, status=status.HTTP_400_BAD_REQUEST
                    )

            # Get next draft order
            next_draft_order = DraftedTeam.objects.filter(league=league).count() + 1

            # Create drafted team entry
            with transaction.atomic():
                drafted_team = DraftedTeam.objects.create(
                    league=league,
                    user=target_user,
                    team_membership=target_membership,
                    team_name=target_membership.team_name,
                    gsis_id=gsis_id,
                    player_name=player_row.get("full_name", "Unknown"),
                    position=player_position,
                    nfl_team=player_row.get("team", "Unknown"),
                    fantasy_points=player_row.get("fantasy_points", 0),
                    draft_order=next_draft_order,
                )

                # Start draft if this is the first pick
                if next_draft_order == 1 and not league.draft_started_at:
                    league.draft_started_at = timezone.now()
                    league.save()

            serializer = DraftedTeamSerializer(drafted_team)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _validate_roster_limits(self, league, team_membership, player_position):
        """
        Validate if a team can draft another player at the given position.
        Returns error message if not allowed, None if allowed.
        """
        if not league.roster_config:
            return None

        # Get current roster for this team
        current_roster = DraftedTeam.objects.filter(
            league=league, team_membership=team_membership
        )

        # Count players by position
        position_counts = {}
        for drafted_player in current_roster:
            pos = drafted_player.position
            position_counts[pos] = position_counts.get(pos, 0) + 1

        logger.info(
            f"ROSTER_VALIDATION: Team {team_membership.team_name} position counts: {position_counts}"
        )
        logger.info(
            f"ROSTER_VALIDATION: Trying to draft {player_position}, league config: {league.roster_config}"
        )

        # Check direct position limit first
        direct_limit = league.roster_config.get(player_position, 0)
        current_at_position = position_counts.get(player_position, 0)

        # For positions with a direct limit, check if it's exceeded
        direct_limit_exceeded = direct_limit > 0 and current_at_position >= direct_limit

        # Check if this position is FLEX-eligible
        flex_config = league.roster_config.get("flex")
        is_flex_eligible = (
            flex_config
            and isinstance(flex_config, dict)
            and player_position in flex_config.get("eligible_positions", [])
        )

        # If direct limit is exceeded OR position has no direct limit but is flex-eligible,
        # check FLEX availability
        if direct_limit_exceeded or (direct_limit == 0 and is_flex_eligible):
            if is_flex_eligible:
                # Check FLEX availability
                flex_count = flex_config.get("count", 0)
                flex_eligible_positions = flex_config.get("eligible_positions", [])

                # Count all flex-eligible players currently on roster
                total_flex_eligible = sum(
                    position_counts.get(pos, 0) for pos in flex_eligible_positions
                )

                # Count players using direct position slots
                used_direct_slots = sum(
                    min(position_counts.get(pos, 0), league.roster_config.get(pos, 0))
                    for pos in flex_eligible_positions
                )

                # Players in FLEX = total eligible - those using direct slots
                players_in_flex = total_flex_eligible - used_direct_slots

                if players_in_flex >= flex_count:
                    return f"Cannot draft {player_position}: FLEX spots are full ({players_in_flex}/{flex_count})"

                # Allow the draft to FLEX
                return None
            else:
                # Position has direct limit but can't use FLEX
                return f"Cannot draft {player_position}: position limit of {direct_limit} reached"

        # If we have a direct limit and haven't exceeded it, allow the draft
        if direct_limit > 0 and current_at_position < direct_limit:
            return None

        # If no direct limit and not flex-eligible, block the draft
        if direct_limit == 0 and not is_flex_eligible:
            return (
                f"Cannot draft {player_position}: position not allowed in this league"
            )

        return None  # Allow the draft

    @action(detail=True, methods=["post"])
    def complete_draft(self, request, pk=None):
        """Complete the draft"""
        league = self.get_object()

        # Check if user is admin
        try:
            membership = LeagueMembership.objects.filter(
                user=request.user, league=league, is_admin=True
            ).first()
            if not membership:
                return Response(
                    {"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {"error": "You are not a member of this league"},
                status=status.HTTP_403_FORBIDDEN,
            )

        league.is_draft_complete = True
        league.draft_completed_at = timezone.now()
        league.save()

        # Build initial cache after draft completion
        try:
            from .cache_utils import refresh_league_cache

            logger.info(
                f"Building initial cache for league {league.id} after draft completion"
            )
            refresh_league_cache(league)
        except Exception as e:
            logger.error(f"Failed to build cache after draft completion: {e}")
            # Don't fail the request, cache will be built on first view

        serializer = self.get_serializer(league)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def undo_draft(self, request, pk=None):
        """Undo the most recent draft pick"""
        league = self.get_object()

        # Check if user is admin
        try:
            membership = LeagueMembership.objects.filter(
                user=request.user, league=league, is_admin=True
            ).first()
            if not membership:
                return Response(
                    {"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {"error": "You are not a member of this league"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if league.is_draft_complete:
            return Response(
                {"error": "Cannot undo draft after completion"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get the most recent draft pick
            most_recent_pick = (
                DraftedTeam.objects.filter(league=league)
                .order_by("-draft_order")
                .first()
            )

            if not most_recent_pick:
                return Response(
                    {"error": "No draft picks to undo"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Delete the most recent pick
            player_name = most_recent_pick.player_name
            team_name = most_recent_pick.team_name
            most_recent_pick.delete()

            # If this was the only pick, reset draft_started_at
            if not DraftedTeam.objects.filter(league=league).exists():
                league.draft_started_at = None
                league.save()

            return Response(
                {
                    "message": f"Undid draft of {player_name} to {team_name}",
                    "success": True,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def reset_draft(self, request, pk=None):
        """Reset the entire draft - delete all draft picks (admin only)"""
        league = self.get_object()

        # Check if user is admin
        membership = LeagueMembership.objects.filter(
            league=league, user=request.user, is_admin=True
        ).first()

        if not membership:
            return Response(
                {"error": "Only league administrators can reset the draft"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Delete all drafted players for this league
            drafted_players = DraftedTeam.objects.filter(league=league)
            player_count = drafted_players.count()

            if player_count == 0:
                return Response(
                    {"error": "No draft picks to reset"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            drafted_players.delete()

            # Reset draft status
            league.draft_started_at = None
            league.draft_completed_at = None
            league.is_draft_complete = False
            league.save()

            return Response(
                {
                    "message": f"Successfully reset draft - removed {player_count} draft picks",
                    "success": True,
                    "players_removed": player_count,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to reset draft: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def drafted_teams(self, request, pk=None):
        """Get all drafted teams organized by user with playoff stats"""
        league = self.get_object()

        try:
            # Import cache utilities
            from .cache_utils import should_refresh_cache, refresh_league_cache
            from .models import CachedPlayerStats

            # Check if cache needs refresh
            needs_refresh, reason = should_refresh_cache(league)

            if needs_refresh:
                logger.info(f"Refreshing cache for league {league.id}: {reason}")
                try:
                    refresh_league_cache(league)
                    logger.info(
                        f"Cache refresh completed successfully for league {league.id}"
                    )
                except Exception as refresh_error:
                    logger.error(
                        f"Cache refresh failed for league {league.id}: {refresh_error}",
                        exc_info=True,
                    )
                    return Response(
                        {
                            "teams": [],
                            "playoff_rounds": [],
                            "message": "Playoff data unavailable. Please try again.",
                        },
                        status=status.HTTP_200_OK,
                    )

            # Query cached stats (fast join query)
            cached_stats = CachedPlayerStats.objects.filter(
                league=league
            ).select_related("cached_player")

            if not cached_stats.exists():
                logger.warning(
                    f"No cache found for league {league.id} after refresh attempt"
                )
                return Response(
                    {
                        "teams": [],
                        "playoff_rounds": [],
                        "message": "Playoff stats not yet available.",
                    },
                    status=status.HTTP_200_OK,
                )

            # Build player results from cache
            player_results = {}

            for stat in cached_stats:
                gsis_id = stat.cached_player.gsis_id

                if gsis_id not in player_results:
                    # Get additional info from DraftedTeam
                    drafted_team = DraftedTeam.objects.filter(
                        league=league, gsis_id=gsis_id
                    ).first()

                    if not drafted_team:
                        continue

                    # Get username
                    username = None
                    if drafted_team.user:
                        username = drafted_team.user.username
                    elif (
                        drafted_team.team_membership
                        and drafted_team.team_membership.user
                    ):
                        username = drafted_team.team_membership.user.username

                    player_results[gsis_id] = {
                        "player_info": {
                            "gsis_id": gsis_id,
                            "player_name": stat.cached_player.player_name,
                            "position": stat.cached_player.position,
                            "nfl_team": stat.cached_player.nfl_team,
                            "team_name": drafted_team.team_name,
                            "user": username,
                            "draft_order": drafted_team.draft_order,
                            "drafted_at": (
                                drafted_team.drafted_at.isoformat()
                                if drafted_team.drafted_at
                                else None
                            ),
                            "id": drafted_team.id,
                        },
                        "round_points": {},
                        "total_points": 0.0,
                    }

                # Add this game's points to the appropriate round
                game_type = stat.game_type
                points = float(stat.fantasy_points)

                player_results[gsis_id]["round_points"][game_type] = (
                    player_results[gsis_id]["round_points"].get(game_type, 0) + points
                )
                player_results[gsis_id]["total_points"] += points

            # Organize by teams and return
            return Response(self._organize_by_teams(player_results, league))

        except Exception as e:
            logger.error(f"Error in drafted_teams cache lookup: {e}")
            import traceback

            traceback.print_exc()
            return self._drafted_teams_fallback(league)

    def _organize_by_teams(self, player_results, league):
        """Helper to organize player results by team"""
        teams = {}
        playoff_rounds = set()

        for gsis_id, player_data in player_results.items():
            player_info = player_data["player_info"]
            team_key = player_info["team_name"]

            playoff_rounds.update(player_data["round_points"].keys())

            if team_key not in teams:
                # Get user data
                user_data = None
                if player_info["user"]:
                    try:
                        user = User.objects.get(username=player_info["user"])
                        user_data = UserSerializer(user).data
                    except User.DoesNotExist:
                        pass

                teams[team_key] = {
                    "user": user_data,
                    "team_name": player_info["team_name"],
                    "players": [],
                    "total_points": 0.0,
                    "round_totals": {},
                }

            # Add player with stats
            player_with_stats = {
                "gsis_id": player_info["gsis_id"],
                "player_name": player_info["player_name"],
                "position": player_info["position"],
                "nfl_team": player_info["nfl_team"],
                "round_points": player_data["round_points"],
                "total_points": player_data["total_points"],
                "fantasy_points": player_data["total_points"],
                "draft_order": player_info["draft_order"],
                "drafted_at": player_info["drafted_at"],
                "id": player_info["id"],
            }

            teams[team_key]["players"].append(player_with_stats)
            teams[team_key]["total_points"] += player_data["total_points"]

            # Add to round totals
            for round_name, round_points in player_data["round_points"].items():
                if round_name not in teams[team_key]["round_totals"]:
                    teams[team_key]["round_totals"][round_name] = 0.0
                teams[team_key]["round_totals"][round_name] += round_points

        # Convert to list and sort
        teams_list = list(teams.values())
        teams_list.sort(key=lambda x: x["total_points"], reverse=True)

        # Sort rounds
        round_order = ["WC", "DIV", "CON", "SB"]
        sorted_rounds = [r for r in round_order if r in playoff_rounds]

        return {
            "teams": teams_list,
            "total_teams": len(teams_list),
            "total_players": sum(len(team["players"]) for team in teams_list),
            "playoff_rounds": sorted_rounds,
            "data_source": "cached_stats",
            "year": league.league_year,
        }

    def _drafted_teams_fallback(self, league):
        """Fallback to original method using real-time calculation"""
        logger.info(f"Using fallback method for league {league.id}")

        # Use new playoff stats calculation
        from .nfl_utils import calculate_player_playoff_points

        # Calculate playoff points for all drafted players
        player_stats = calculate_player_playoff_points(league, None)

        if player_stats:
            # Organize by teams using playoff stats
            teams = {}
            playoff_rounds = set()

            for player_id, player_data in player_stats.items():
                player_info = player_data["player_info"]
                # Use team_name as the key to avoid duplicates when users claim teams
                team_key = player_info["team_name"]

                # Add to playoff rounds set
                playoff_rounds.update(player_data["round_points"].keys())

                if team_key not in teams:
                    # Find user data for this team
                    user_data = None
                    if player_info["user"]:
                        try:
                            user = User.objects.get(username=player_info["user"])
                            user_data = UserSerializer(user).data
                        except User.DoesNotExist:
                            pass

                    teams[team_key] = {
                        "user": user_data,
                        "team_name": player_info["team_name"],
                        "players": [],
                        "total_points": 0.0,
                        "round_totals": {},
                    }

                # Add player with playoff stats
                player_with_stats = {
                    "gsis_id": player_info["gsis_id"],
                    "player_name": player_info["player_name"],
                    "position": player_info["position"],
                    "nfl_team": player_info["nfl_team"],
                    "round_points": player_data["round_points"],
                    "total_points": player_data["total_points"],
                    "fantasy_points": player_data["total_points"],
                    "draft_order": player_info["draft_order"],
                    "drafted_at": player_info["drafted_at"],
                    "id": player_info["id"],
                }

                teams[team_key]["players"].append(player_with_stats)
                teams[team_key]["total_points"] += player_data["total_points"]

                # Add to round totals
                for round_name, round_points in player_data["round_points"].items():
                    if round_name not in teams[team_key]["round_totals"]:
                        teams[team_key]["round_totals"][round_name] = 0.0
                    teams[team_key]["round_totals"][round_name] += round_points

            # Convert to list and sort by total points
            teams_list = list(teams.values())
            teams_list.sort(key=lambda x: x["total_points"], reverse=True)

            # Sort playoff rounds
            round_order = ["WC", "DIV", "CON", "SB"]
            sorted_rounds = [r for r in round_order if r in playoff_rounds]

            return Response(
                {
                    "teams": teams_list,
                    "total_teams": len(teams_list),
                    "total_players": sum(len(team["players"]) for team in teams_list),
                    "playoff_rounds": sorted_rounds,
                    "data_source": "fallback_stats",
                    "year": league.league_year,
                }
            )

        # Fallback to static points if no playoff stats available
        drafted_players = DraftedTeam.objects.filter(league=league).order_by(
            "draft_order"
        )

        # Group by team_name to avoid duplicates when users claim teams
        teams = {}
        for player in drafted_players:
            team_key = player.team_name

            if team_key not in teams:
                # Get user data from either player.user or team_membership.user
                user_data = None
                if player.user:
                    user_data = UserSerializer(player.user).data
                elif player.team_membership and player.team_membership.user:
                    user_data = UserSerializer(player.team_membership.user).data

                teams[team_key] = {
                    "user": user_data,
                    "team_name": player.team_name,
                    "players": [],
                    "total_points": 0,
                }

            player_data = DraftedTeamSerializer(player).data
            teams[team_key]["players"].append(player_data)
            teams[team_key]["total_points"] += player.fantasy_points

        # Convert to list and sort by total points
        teams_list = list(teams.values())
        teams_list.sort(key=lambda x: x["total_points"], reverse=True)

        return Response(
            {
                "teams": teams_list,
                "total_teams": len(teams_list),
                "total_players": drafted_players.count(),
                "data_source": "static_points",
            }
        )

    @action(detail=True, methods=["get"])
    def scoring_settings(self, request, pk=None):
        """Get league's custom scoring settings"""
        league = self.get_object()

        # Get custom scoring settings for this league
        scoring_settings = league.custom_scoring_settings.all()

        # Debug logging
        logger.info(
            f"League {league.id} has {scoring_settings.count()} scoring settings"
        )

        # If no custom settings exist, create default ones now
        if scoring_settings.count() == 0:
            logger.info(f"Creating default scoring settings for league {league.id}")
            self._create_default_scoring_settings(league)
            scoring_settings = league.custom_scoring_settings.all()
            logger.info(
                f"After creating defaults, league has {scoring_settings.count()} scoring settings"
            )

        # Get default configurations for increment_value and display_name
        all_defaults = {**SCORING_MULTIPLIERS, **DEFENSE_SCORING_MULTIPLIERS}

        # Group by category with enforced order
        categorized_settings = {}
        for setting in scoring_settings:
            category = setting.category or "Miscellaneous"
            if category not in categorized_settings:
                categorized_settings[category] = []

            # Get increment_value and display_name from default config (if available)
            increment_value = 0.01  # default fallback
            display_name = setting.display_name  # fallback to stored name

            if setting.stat_name in all_defaults:
                increment_value = all_defaults[setting.stat_name]["increment_value"]
                display_name = all_defaults[setting.stat_name]["display_name"]

            categorized_settings[category].append(
                {
                    "id": setting.id,
                    "stat_name": setting.stat_name,
                    "display_name": display_name,
                    "multiplier": setting.multiplier,
                    "increment_value": increment_value,
                    "is_defensive_stat": setting.is_defensive_stat,
                }
            )

        # Define category order and return ordered dictionary
        category_order = [
            "Passing",
            "Rushing",
            "Receiving",
            "Defense/Special Teams",
            "Kicking",
            "Returns",
            "Miscellaneous",
        ]

        # Create ordered categorized settings
        ordered_settings = {}
        for category in category_order:
            if category in categorized_settings:
                ordered_settings[category] = categorized_settings[category]

        return Response({"league_id": league.id, "scoring_settings": ordered_settings})

    @action(detail=True, methods=["post", "put"])
    def update_scoring_settings(self, request, pk=None):
        """Update league's scoring settings (admin only)"""
        league = self.get_object()

        # Check if user is admin
        user_membership = LeagueMembership.objects.filter(
            user=request.user, league=league
        ).first()
        if not user_membership or not user_membership.is_admin:
            return Response(
                {"error": "Only league administrators can update scoring settings"},
                status=status.HTTP_403_FORBIDDEN,
            )

        scoring_updates = request.data.get("scoring_settings", [])

        if not scoring_updates:
            return Response(
                {"error": "No scoring settings provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        updated_settings = []

        for update in scoring_updates:
            stat_name = update.get("stat_name")
            multiplier = update.get("multiplier")

            if stat_name is None or multiplier is None:
                continue

            try:
                # Get or create the setting
                setting, created = LeagueScoringSetting.objects.get_or_create(
                    league=league,
                    stat_name=stat_name,
                    defaults={
                        "multiplier": multiplier,
                        "is_defensive_stat": update.get("is_defensive_stat", False),
                        "category": update.get("category", ""),
                        "display_name": update.get("display_name", stat_name),
                    },
                )

                if not created:
                    # Update existing setting
                    setting.multiplier = multiplier
                    setting.save()

                updated_settings.append(
                    {
                        "stat_name": setting.stat_name,
                        "multiplier": setting.multiplier,
                        "display_name": setting.display_name,
                    }
                )

            except Exception as e:
                return Response(
                    {"error": f"Error updating {stat_name}: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Invalidate cache after scoring settings are updated
        from .models import CachedPlayerStats

        deleted_count = CachedPlayerStats.objects.filter(league=league).delete()[0]
        logger.info(
            f"Scoring settings updated for league {league.id}. "
            f"Cleared {deleted_count} cached entries. "
            f"Cache will be rebuilt on next request."
        )

        return Response(
            {
                "message": f"Updated {len(updated_settings)} scoring settings",
                "updated_settings": updated_settings,
                "cache_invalidated": True,
                "cached_entries_cleared": deleted_count,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.AllowAny])
    def manual_refresh_cache(self, request, pk=None):
        """Manually trigger cache refresh for a league"""
        league = self.get_object()

        try:
            from .cache_utils import refresh_league_cache

            logger.info(
                f"Manual cache refresh triggered for league {league.id} by user request"
            )
            refresh_league_cache(league)
            logger.info(f"Manual cache refresh completed for league {league.id}")

            return Response(
                {
                    "message": "Cache refreshed successfully",
                    "league_id": league.id,
                    "status": "success",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(
                f"Manual cache refresh failed for league {league.id}: {e}",
                exc_info=True,
            )
            return Response(
                {
                    "error": "Failed to refresh cache",
                    "details": "An internal error occurred while refreshing the cache.",
                    "status": "error",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], permission_classes=[permissions.AllowAny])
    def playoff_stats(self, request, pk=None):
        """Get playoff stats for all drafted players with calculated fantasy points (with PostgreSQL caching)"""
        league = self.get_object()

        try:
            # Import cache utilities
            from .cache_utils import should_refresh_cache, refresh_league_cache
            from .models import CachedPlayerStats

            # Check if cache needs refresh
            needs_refresh, reason = should_refresh_cache(league)

            if needs_refresh:
                logger.info(f"Refreshing cache for league {league.id}: {reason}")
                try:
                    refresh_league_cache(league)
                    logger.info(
                        f"Cache refresh completed successfully for league {league.id}"
                    )
                except Exception as refresh_error:
                    logger.error(
                        f"Cache refresh failed for league {league.id}: {refresh_error}",
                        exc_info=True,
                    )
                    return Response(
                        {
                            "teams": [],
                            "playoff_rounds": [],
                            "total_teams": 0,
                            "message": "Playoff data unavailable. Please try again.",
                        },
                        status=status.HTTP_200_OK,
                    )

            # Pre-fetch ALL drafted teams in a single query to avoid N+1 problem
            drafted_teams = DraftedTeam.objects.filter(league=league).select_related(
                "user", "team_membership__user"
            )

            # Build lookup dictionary by gsis_id for O(1) access
            drafted_teams_by_gsis = {dt.gsis_id: dt for dt in drafted_teams}

            # Query cached stats (fast join query)
            cached_stats = CachedPlayerStats.objects.filter(
                league=league
            ).select_related("cached_player")

            if not cached_stats.exists():
                logger.warning(
                    f"No cache found for league {league.id} after refresh attempt"
                )
                return Response(
                    {
                        "teams": [],
                        "playoff_rounds": [],
                        "total_teams": 0,
                        "message": "Playoff stats not yet available.",
                    },
                    status=status.HTTP_200_OK,
                )

            # Build player results from cache
            player_results = {}

            for stat in cached_stats:
                gsis_id = stat.cached_player.gsis_id

                if gsis_id not in player_results:
                    # Fast lookup from pre-fetched dictionary (O(1))
                    drafted_team = drafted_teams_by_gsis.get(gsis_id)

                    if not drafted_team:
                        continue

                    # Get username
                    username = None
                    if drafted_team.user:
                        username = drafted_team.user.username
                    elif (
                        drafted_team.team_membership
                        and drafted_team.team_membership.user
                    ):
                        username = drafted_team.team_membership.user.username

                    player_results[gsis_id] = {
                        "player_info": {
                            "gsis_id": gsis_id,
                            "player_name": stat.cached_player.player_name,
                            "position": stat.cached_player.position,
                            "nfl_team": stat.cached_player.nfl_team,
                            "team_name": drafted_team.team_name,
                            "user": username,
                        },
                        "round_points": {},
                        "total_points": 0.0,
                        "is_eliminated": False,  # Will be updated if any game is eliminated
                    }

                # Add this game's points to the appropriate round
                game_type = stat.game_type
                points = float(stat.fantasy_points)

                # Update elimination status (if any game is eliminated, player is eliminated)
                if stat.is_eliminated:
                    player_results[gsis_id]["is_eliminated"] = True

                player_results[gsis_id]["round_points"][game_type] = (
                    player_results[gsis_id]["round_points"].get(game_type, 0) + points
                )
                player_results[gsis_id]["total_points"] += points

            # Organize by teams
            teams = {}
            playoff_rounds = set()

            for player_id, player_data in player_results.items():
                player_info = player_data["player_info"]
                user_key = (
                    player_info["user"]
                    if player_info["user"]
                    else f"unclaimed_{player_info['team_name']}"
                )

                playoff_rounds.update(player_data["round_points"].keys())

                if user_key not in teams:
                    teams[user_key] = {
                        "user": player_info["user"],
                        "team_name": player_info["team_name"],
                        "players": [],
                        "total_points": 0.0,
                        "round_totals": {},
                    }

                # Add player with playoff stats
                player_with_stats = {
                    "gsis_id": player_info["gsis_id"],
                    "player_name": player_info["player_name"],
                    "position": player_info["position"],
                    "nfl_team": player_info["nfl_team"],
                    "round_points": player_data["round_points"],
                    "total_points": player_data["total_points"],
                    "is_eliminated": player_data.get("is_eliminated", False),
                }

                teams[user_key]["players"].append(player_with_stats)
                teams[user_key]["total_points"] += player_data["total_points"]

                # Add to round totals
                for round_name, round_points in player_data["round_points"].items():
                    if round_name not in teams[user_key]["round_totals"]:
                        teams[user_key]["round_totals"][round_name] = 0.0
                    teams[user_key]["round_totals"][round_name] += round_points

            # Convert to list and sort by total points
            teams_list = list(teams.values())
            teams_list.sort(key=lambda x: x["total_points"], reverse=True)

            # Sort playoff rounds
            round_order = ["WC", "DIV", "CON", "SB"]
            sorted_rounds = [r for r in round_order if r in playoff_rounds]

            return Response(
                {
                    "teams": teams_list,
                    "playoff_rounds": sorted_rounds,
                    "total_teams": len(teams_list),
                    "year": league.league_year,
                    "data_source": "cached_stats",
                }
            )

        except Exception as e:
            logger.error(f"Error in playoff_stats cache lookup: {e}", exc_info=True)
            return self._playoff_stats_fallback(league, request)

    def _playoff_stats_fallback(self, league, request):
        """Fallback method for playoff_stats using real-time calculation"""
        logger.info(f"Using fallback method for playoff_stats in league {league.id}")

        try:
            from .nfl_utils import calculate_player_playoff_points

            # Get year from query params or use league year
            year = request.query_params.get("year")
            if year:
                try:
                    year = int(year)
                except ValueError:
                    return Response(
                        {"error": "Invalid year parameter"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Calculate playoff points for all drafted players
            player_stats = calculate_player_playoff_points(league, year)

            if not player_stats:
                return Response(
                    {
                        "message": "No playoff stats available for this year",
                        "teams": [],
                        "playoff_rounds": [],
                        "data_source": "fallback",
                    }
                )

            # Organize by teams
            teams = {}
            playoff_rounds = set()

            for player_id, player_data in player_stats.items():
                player_info = player_data["player_info"]
                user_key = (
                    player_info["user"]
                    if player_info["user"]
                    else f"unclaimed_{player_info['team_name']}"
                )

                playoff_rounds.update(player_data["round_points"].keys())

                if user_key not in teams:
                    teams[user_key] = {
                        "user": player_info["user"],
                        "team_name": player_info["team_name"],
                        "players": [],
                        "total_points": 0.0,
                        "round_totals": {},
                    }

                # Add player with playoff stats
                player_with_stats = {
                    "gsis_id": player_info["gsis_id"],
                    "player_name": player_info["player_name"],
                    "position": player_info["position"],
                    "nfl_team": player_info["nfl_team"],
                    "round_points": player_data["round_points"],
                    "total_points": player_data["total_points"],
                    "is_eliminated": player_data.get("is_eliminated", False),
                }

                teams[user_key]["players"].append(player_with_stats)
                teams[user_key]["total_points"] += player_data["total_points"]

                # Add to round totals
                for round_name, round_points in player_data["round_points"].items():
                    if round_name not in teams[user_key]["round_totals"]:
                        teams[user_key]["round_totals"][round_name] = 0.0
                    teams[user_key]["round_totals"][round_name] += round_points

            # Convert to list and sort by total points
            teams_list = list(teams.values())
            teams_list.sort(key=lambda x: x["total_points"], reverse=True)

            # Sort playoff rounds
            round_order = ["WC", "DIV", "CON", "SB"]
            sorted_rounds = [r for r in round_order if r in playoff_rounds]

            return Response(
                {
                    "teams": teams_list,
                    "playoff_rounds": sorted_rounds,
                    "total_teams": len(teams_list),
                    "year": year or league.league_year,
                    "data_source": "fallback",
                }
            )

        except Exception as e:
            logger.error(f"Error in playoff_stats fallback: {e}", exc_info=True)
            return Response(
                {"error": f"Failed to get playoff stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        """Delete a league (admin only)"""
        league = self.get_object()

        # Check if user is the creator or an admin
        is_creator = league.created_by == request.user
        is_admin = LeagueMembership.objects.filter(
            user=request.user, league=league, is_admin=True
        ).exists()

        if not (is_creator or is_admin):
            return Response(
                {
                    "error": "Only league administrators or the league creator can delete the league"
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Delete the league (this will cascade delete all related data)
        league_name = league.name
        league.delete()

        return Response(
            {"message": f"League '{league_name}' has been successfully deleted"},
            status=status.HTTP_200_OK,
        )


class LeagueMembershipViewSet(viewsets.ModelViewSet):
    serializer_class = LeagueMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return LeagueMembership.objects.filter(user=self.request.user)


class DraftedTeamViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DraftedTeamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return drafted players from leagues the user is in
        user_leagues = League.objects.filter(members__user=self.request.user)
        return DraftedTeam.objects.filter(league__in=user_leagues)


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def available_league_years(request):
    """
    API endpoint to get available years from PlayoffDraftablePlayer table.

    Returns:
        JsonResponse: JSON response containing available years sorted in descending order

    Example response:
        {
            "available_years": [2025, 2024, 2023],
            "status": "success"
        }
    """
    try:
        years = (
            PlayoffDraftablePlayer.objects.values_list("year", flat=True)
            .distinct()
            .order_by("-year")
        )
        return Response({"available_years": list(years), "status": "success"})
    except Exception as e:
        return Response({"error": str(e), "status": "error"}, status=500)
