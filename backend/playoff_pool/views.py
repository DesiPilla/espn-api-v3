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

from .models import League, LeagueMembership, DraftedTeam, UserProfile
from backend.playoff_pool.players import query_playoff_players_from_db
from backend.playoff_pool.scoring import SCORING_MULTIPLIERS

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
    """Get default scoring settings"""
    return Response(
        {
            "scoring_multipliers": SCORING_MULTIPLIERS,
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

        return Response(
            LeagueMembershipSerializer(team).data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["delete"], url_path="teams/(?P<team_id>[^/.]+)")
    def remove_team(self, request, pk=None, team_id=None):
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
            nfl_year = 2025
            positions = (
                league.positions_included
                if league.positions_included
                else ["QB", "RB", "WR", "TE", "K", "DST"]
            )
            available_players = query_playoff_players_from_db(
                year=nfl_year, positions_to_keep=positions
            )
            # Map full_name to name for frontend compatibility
            for player in available_players:
                player["name"] = player.get("full_name", "")
            # available_players is already a list of dicts
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
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

        # Get player info
        try:
            nfl_year = 2025
            positions = (
                league.positions_included
                if league.positions_included
                else ["QB", "RB", "WR", "TE", "K", "DST"]
            )

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
                    position=player_row.get("position", "Unknown"),
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

    @action(detail=True, methods=["get"])
    def drafted_teams(self, request, pk=None):
        """Get all drafted teams organized by user"""
        league = self.get_object()

        # Get all drafted players
        drafted_players = DraftedTeam.objects.filter(league=league).order_by(
            "draft_order"
        )

        # Group by user
        teams = {}
        for player in drafted_players:
            # Handle both claimed and unclaimed teams
            if player.user:
                user_id = player.user.id
                user_data = UserSerializer(player.user).data
            else:
                # For unclaimed teams, use team_membership id as identifier
                user_id = f"unclaimed_{player.team_membership.id}"
                user_data = None

            if user_id not in teams:
                teams[user_id] = {
                    "user": user_data,
                    "team_name": player.team_name,
                    "players": [],
                    "total_points": 0,
                }

            player_data = DraftedTeamSerializer(player).data
            teams[user_id]["players"].append(player_data)
            teams[user_id]["total_points"] += player.fantasy_points

        # Convert to list and sort by total points
        teams_list = list(teams.values())
        teams_list.sort(key=lambda x: x["total_points"], reverse=True)

        return Response(
            {
                "teams": teams_list,
                "total_teams": len(teams_list),
                "total_players": drafted_players.count(),
            }
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
