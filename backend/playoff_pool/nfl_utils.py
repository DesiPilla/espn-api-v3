"""
NFL utility functions for playoff pool application.
"""
from backend.playoff_pool.players import get_defense_stats
from backend.playoff_pool.scoring import (
    calculate_fantasy_points,
    get_league_scoring_settings,
    DEFENSE_SCORING_MULTIPLIERS,
)
import nflreadpy as nfl
import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

# Playoff teams for each year
PLAYOFF_TEAMS = {
    2024: [
        "KC",
        "BUF",
        "BAL",
        "HOU",
        "LAC",
        "PIT",
        "DEN",
        "DET",
        "PHI",
        "TB",
        "LA",  # Rams are encoded as "LA" in nflreadpy
        "MIN",
        "WAS",
        "GB",
    ],
    2025: [  # Add 2025 teams when known
        # Will need to be updated when playoffs are set
    ],
}


def get_current_nfl_season():
    """
    Get the current NFL season year.
    
    Returns:
        int: The current NFL season year
    
    Example:
        >>> season = get_current_nfl_season()
        >>> print(season)
        2025
    """
    return nfl.get_current_season()


@api_view(['GET'])
@permission_classes([AllowAny])
def current_nfl_season_api(request):
    """
    API endpoint to get the current NFL season year.
    
    Returns:
        JsonResponse: JSON response containing the current season year
        
    Example response:
        {
            "current_season": 2025,
            "status": "success"
        }
    """
    try:
        current_season = get_current_nfl_season()
        return JsonResponse({
            'current_season': current_season,
            'status': 'success'
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)


def calculate_player_playoff_points(league, year=None):
    """
    Calculate playoff fantasy points for all drafted players in a league.
    Uses caching to avoid expensive NFL data loads and recalculations.

    Args:
        league: League model instance
        year (int, optional): Season year. Defaults to league's year.

    Returns:
        dict: Player stats with calculated fantasy points by playoff round
    """
    try:
        if year is None:
            year = league.league_year

        # NOTE: Old Django cache removed - now using PostgreSQL cache tables
        # Cache is managed by cache_utils.py and views.py

        nfl_cached_data = None

        if True:  # Always fetch fresh data (will be cached in DB by cache_utils)
            # Get weekly stats for playoff weeks (with Django caching)
            from django.core.cache import cache

            cache_key = f"nfl_player_stats_{year}"
            weekly_stats = cache.get(cache_key)

            if weekly_stats is None:
                weekly_stats = nfl.load_player_stats([year]).to_pandas()
                # Cache for 1 hour (3600 seconds)
                cache.set(cache_key, weekly_stats, 3600)

            defense_stats = get_defense_stats(year)
            defense_stats["player_name"] = defense_stats["full_name"]
            defense_stats["player_display_name"] = defense_stats["full_name"]
            defense_stats["position_group"] = "DEF"

            weekly_stats = pd.concat([weekly_stats, defense_stats])
            weekly_stats = weekly_stats[weekly_stats["season_type"] == "POST"]

            if weekly_stats.empty:
                print(f"Debug: No playoff stats found for year {year}")
                return {}

            # Get playoff schedule to map weeks to game types
            week_map = {
                19: "WC",
                20: "DIV",
                21: "CON",
                22: "SB",
            }
            weekly_stats["game_type"] = weekly_stats["week"].map(week_map)

            # Note: No longer caching in Django - using DB cache instead
            nfl_cached_data = {
                "weekly_stats": weekly_stats,
                "week_to_game_type": week_map,
            }

        # Unpack NFL data
        weekly_stats = nfl_cached_data["weekly_stats"]
        week_to_game_type = nfl_cached_data["week_to_game_type"]

        # Get league scoring settings
        scoring_settings = get_league_scoring_settings(league)

        # Get drafted players
        from .models import DraftedTeam

        drafted_players = DraftedTeam.objects.filter(league=league)

        # Calculate points for each player
        player_results = {}

        # Process regular (non-D/ST) players
        for drafted_player in drafted_players:
            gsis_id = drafted_player.gsis_id

            # Format drafted_at in EST if available
            drafted_at_est = None
            if drafted_player.drafted_at:
                import pytz

                est = pytz.timezone("America/New_York")
                drafted_at_est = drafted_player.drafted_at.astimezone(est).isoformat()

            # Get username from user or team_membership
            username = None
            if drafted_player.user:
                username = drafted_player.user.username
            elif drafted_player.team_membership and drafted_player.team_membership.user:
                username = drafted_player.team_membership.user.username

            player_results[gsis_id] = {
                "player_info": {
                    "gsis_id": drafted_player.gsis_id,
                    "player_name": drafted_player.player_name,
                    "position": drafted_player.position,
                    "nfl_team": drafted_player.nfl_team,
                    "team_name": drafted_player.team_name,
                    "user": username,
                    "draft_order": drafted_player.draft_order,
                    "drafted_at": (
                        drafted_player.drafted_at.isoformat()
                        if drafted_player.drafted_at
                        else None
                    ),
                    "drafted_at_est": drafted_at_est,
                    "id": drafted_player.id,
                },
                "round_points": {},
                "total_points": 0.0,
            }

            total_points = 0.0

            # Calculate points for each playoff round
            for week, round_stats in weekly_stats.groupby("week"):
                if week not in week_to_game_type:
                    continue

                game_type = week_to_game_type[week]
                round_points = 0.0

                # Find player's stats for this round
                # Use safe column access to avoid KeyError
                player_round_stats = round_stats

                # Try different ID matching strategies with safe column access
                # WARNING! DraftedTeams only has gsis_id, but load_stats() only has player_id
                # You could join to DraftablePlayer to get player_id, but for now we'll just use player_name
                # round_stats.to_csv("debug_round_stats.csv")  # Debug output
                player_round_stats = round_stats[
                    (round_stats["player_display_name"] == drafted_player.player_name)
                    & (round_stats["position"] == drafted_player.position)
                    & (round_stats["team"] == drafted_player.nfl_team)
                ]
                if player_round_stats.empty:
                    print(
                        f"Debug: No stats found for player {drafted_player.player_name} ({drafted_player.nfl_team}) in week {week} ({game_type})"
                    )
                    continue

                # Calculate points for this round
                for _, row in player_round_stats.iterrows():
                    round_points += calculate_fantasy_points(row, scoring_settings)

                if game_type not in player_results[gsis_id]["round_points"]:
                    player_results[gsis_id]["round_points"][game_type] = 0.0

                player_results[gsis_id]["round_points"][game_type] += round_points
                total_points += round_points

            player_results[gsis_id]["total_points"] = total_points

        # Note: No longer caching in Django - using DB cache instead (see cache_utils.py)
        return player_results

    except Exception as e:
        print(f"Error in calculate_player_playoff_points: {e}")
        import traceback

        traceback.print_exc()
        return {}
