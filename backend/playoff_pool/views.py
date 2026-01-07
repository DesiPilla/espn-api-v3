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

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def debug_test(request):
    """Debug endpoint to test routing"""
    logger.info(f"DEBUG_TEST: Received {request.method} request")
    return Response({
        'message': f'Debug endpoint reached with {request.method} method',
        'path': request.path,
        'method': request.method
    })
from .serializers import (
    LeagueSerializer, LeagueMembershipSerializer, DraftedTeamSerializer,
    UserRegistrationSerializer, UserSerializer, DraftPlayerSerializer,
    AvailablePlayerSerializer
)
from backend.playoff_pool.players import get_all_playoff_players
from backend.playoff_pool.scoring import SCORING_MULTIPLIERS


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    """Login user and return auth token"""
    logger.info(f"LOGIN_USER: Received {request.method} request to login_user")
    logger.info(f"LOGIN_USER: Request data: {request.data}")
    logger.info(f"LOGIN_USER: Request headers: {dict(request.headers)}")
    
    username = request.data.get('username')
    password = request.data.get('password')
    
    logger.info(f"LOGIN_USER: Username: {username}, Password length: {len(password) if password else 0}")
    
    if not username or not password:
        return Response({
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        # Get or create user profile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': profile.display_name
            }
        })
    else:
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
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
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'display_name': profile.display_name
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ensure_csrf_cookie
@api_view(['GET'])
def scoring_settings(request):
    """Get default scoring settings"""
    return Response({
        'scoring_multipliers': SCORING_MULTIPLIERS,
        'position_choices': [
            {'value': 'QB', 'label': 'Quarterback'},
            {'value': 'RB', 'label': 'Running Back'},
            {'value': 'WR', 'label': 'Wide Receiver'},
            {'value': 'TE', 'label': 'Tight End'},
            {'value': 'K', 'label': 'Kicker'},
            {'value': 'DST', 'label': 'Defense/Special Teams'},
        ]
    })


class LeagueViewSet(viewsets.ModelViewSet):
    serializer_class = LeagueSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Add debugging for authentication"""
        logger.info(f"LEAGUE_VIEWSET: {request.method} request to {request.path}")
        logger.info(f"LEAGUE_VIEWSET: Headers: {dict(request.headers)}")
        logger.info(f"LEAGUE_VIEWSET: User: {request.user}")
        logger.info(f"LEAGUE_VIEWSET: User authenticated: {request.user.is_authenticated}")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        # Only return leagues the user is a member of
        return League.objects.filter(
            members__user=self.request.user
        ).distinct()
    
    def perform_create(self, serializer):
        # Create league with current user as creator
        league = serializer.save(created_by=self.request.user)
        
        # Add creator as admin member
        LeagueMembership.objects.create(
            user=self.request.user,
            league=league,
            team_name=f"{self.request.user.username}'s Team",
            is_admin=True
        )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a league"""
        league = self.get_object()
        team_name = request.data.get('team_name', f"{request.user.username}'s Team")
        
        # Check if user is already in league
        if LeagueMembership.objects.filter(user=request.user, league=league).exists():
            return Response({'error': 'You are already a member of this league'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if league is full
        current_members = LeagueMembership.objects.filter(league=league).count()
        if current_members >= league.num_teams:
            return Response({'error': 'This league is full'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        membership = LeagueMembership.objects.create(
            user=request.user,
            league=league,
            team_name=team_name
        )
        
        return Response(LeagueMembershipSerializer(membership).data, 
                       status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get league members"""
        league = self.get_object()
        members = LeagueMembership.objects.filter(league=league).select_related('user')
        serializer = LeagueMembershipSerializer(members, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def available_players(self, request, pk=None):
        """Get available players for drafting"""
        league = self.get_object()
        
        try:
            # Use 2025 as the most recent complete NFL season
            # TODO: Make this configurable or automatically detect latest available year
            nfl_year = 2025
            
            # Use default positions if none specified
            positions = league.positions_included if league.positions_included else ["QB", "RB", "WR", "TE", "K", "DST"]
            
            available_players_df = get_all_playoff_players(
                year=nfl_year,
                positions_to_keep=positions
            )
            
            # Convert to list of dicts
            available_players = []
            for _, player in available_players_df.iterrows():
                available_players.append({
                    'player_id': str(player.get('player_id', player.get('gsis_id', ''))),
                    'name': player.get('full_name', 'Unknown'),
                    'position': player.get('position', 'Unknown'),
                    'team': player.get('team', 'Unknown'),
                    'fantasy_points': round(player.get('fantasy_points', 0), 2)
                })
            
            # Remove already drafted players
            drafted_player_ids = DraftedTeam.objects.filter(
                league=league
            ).values_list('player_id', flat=True)
            available_players = [
                p for p in available_players 
                if p['player_id'] not in drafted_player_ids
            ]
            
            # Sort by fantasy points in descending order
            available_players.sort(key=lambda x: -x['fantasy_points'])
            
            serializer = AvailablePlayerSerializer(available_players, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def draft_player(self, request, pk=None):
        """Draft a player to a team"""
        league = self.get_object()
        
        # Check if user is admin
        try:
            membership = LeagueMembership.objects.get(user=request.user, league=league)
            if not membership.is_admin:
                return Response({'error': 'Admin access required'}, 
                              status=status.HTTP_403_FORBIDDEN)
        except LeagueMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this league'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if league.is_draft_complete:
            return Response({'error': 'Draft is already complete'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DraftPlayerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        player_id = serializer.validated_data['player_id']
        user_id = serializer.validated_data['user_id']
        
        try:
            target_user = User.objects.get(id=user_id)
            target_membership = LeagueMembership.objects.get(user=target_user, league=league)
        except (User.DoesNotExist, LeagueMembership.DoesNotExist):
            return Response({'error': 'Invalid user or user not in league'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Check if player is already drafted
        if DraftedTeam.objects.filter(league=league, player_id=player_id).exists():
            return Response({'error': 'Player already drafted'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get player info
        try:
            # Use 2025 as the most recent complete NFL season
            nfl_year = 2025
            
            # Use default positions if none specified
            positions = league.positions_included if league.positions_included else ["QB", "RB", "WR", "TE", "K", "DST"]
            
            available_players_df = get_all_playoff_players(
                year=nfl_year,
                positions_to_keep=positions
            )
            
            player_row = None
            for _, player in available_players_df.iterrows():
                if str(player.get('player_id', player.get('gsis_id', ''))) == player_id:
                    player_row = player
                    break
            
            if player_row is None:
                return Response({'error': 'Player not found'}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            # Get next draft order
            next_draft_order = DraftedTeam.objects.filter(league=league).count() + 1
            
            # Create drafted team entry
            with transaction.atomic():
                drafted_team = DraftedTeam.objects.create(
                    league=league,
                    user=target_user,
                    team_name=target_membership.team_name,
                    player_id=player_id,
                    player_name=player_row.get('full_name', 'Unknown'),
                    position=player_row.get('position', 'Unknown'),
                    team=player_row.get('team', 'Unknown'),
                    fantasy_points=player_row.get('fantasy_points', 0),
                    draft_order=next_draft_order
                )
                
                # Start draft if this is the first pick
                if next_draft_order == 1 and not league.draft_started_at:
                    league.draft_started_at = timezone.now()
                    league.save()
            
            serializer = DraftedTeamSerializer(drafted_team)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def complete_draft(self, request, pk=None):
        """Complete the draft"""
        league = self.get_object()
        
        # Check if user is admin
        try:
            membership = LeagueMembership.objects.get(user=request.user, league=league)
            if not membership.is_admin:
                return Response({'error': 'Admin access required'}, 
                              status=status.HTTP_403_FORBIDDEN)
        except LeagueMembership.DoesNotExist:
            return Response({'error': 'You are not a member of this league'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        league.is_draft_complete = True
        league.draft_completed_at = timezone.now()
        league.save()
        
        serializer = self.get_serializer(league)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def drafted_teams(self, request, pk=None):
        """Get all drafted teams organized by user"""
        league = self.get_object()
        
        # Get all drafted players
        drafted_players = DraftedTeam.objects.filter(league=league).order_by('draft_order')
        
        # Group by user
        teams = {}
        for player in drafted_players:
            user_id = player.user.id
            if user_id not in teams:
                teams[user_id] = {
                    'user': UserSerializer(player.user).data,
                    'team_name': player.team_name,
                    'players': [],
                    'total_points': 0
                }
            
            player_data = DraftedTeamSerializer(player).data
            teams[user_id]['players'].append(player_data)
            teams[user_id]['total_points'] += player.fantasy_points
        
        # Convert to list and sort by total points
        teams_list = list(teams.values())
        teams_list.sort(key=lambda x: x['total_points'], reverse=True)
        
        return Response({
            'teams': teams_list,
            'total_teams': len(teams_list),
            'total_players': drafted_players.count()
        })


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