"""
NFL utility functions for playoff pool application.
"""
from backend.playoff_pool.scoring import (
    calculate_fantasy_points,
    get_league_scoring_settings,
)
import nflreadpy as nfl
import pandas as pd
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


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

    Args:
        league: League model instance
        year (int, optional): Season year. Defaults to league's year.

    Returns:
        dict: Player stats with calculated fantasy points by playoff round
    """
    try:
        if year is None:
            year = league.league_year

        # Get weekly stats for playoff weeks
        weekly_stats = nfl.load_player_stats([year]).to_pandas()
        weekly_stats = weekly_stats[weekly_stats["season_type"] == "POST"]

        # Debug: Print column names to understand data structure
        print(
            f"Debug: Available columns in weekly_stats: {list(weekly_stats.columns)[:10]}..."
        )  # Show first 10

        if weekly_stats.empty:
            print(f"Debug: No playoff stats found for year {year}")
            return {}

        # Get playoff schedule to map weeks to game types
        try:
            schedule = nfl.import_schedules([year])
            playoff_games = schedule[schedule["playoff"] == 1].copy()

            if playoff_games.empty:
                print(f"Debug: No playoff games found in schedule for year {year}")
                return {}

            # Create week to game type mapping
            playoff_games = playoff_games.sort_values("week")
            playoff_weeks = sorted(playoff_games["week"].unique())

            week_to_game_type = {}
            for i, week in enumerate(playoff_weeks):
                week_games = playoff_games[playoff_games["week"] == week]
                num_games = len(week_games)

                # Determine game type based on number of games and position
                if i == 0 and num_games >= 4:
                    game_type = "WC"  # Wild Card
                elif (i == 1 and num_games == 4) or (i == 0 and num_games == 4):
                    game_type = "DIV"  # Divisional Round
                elif num_games == 2:
                    game_type = "CON"  # Conference Championship
                elif num_games == 1:
                    game_type = "SB"  # Super Bowl
                else:
                    # Fallback based on position
                    if i == 0:
                        game_type = "WC"
                    elif i == 1:
                        game_type = "DIV"
                    elif i == 2:
                        game_type = "CON"
                    else:
                        game_type = "SB"

                week_to_game_type[week] = game_type
        except Exception as e:
            print(f"Warning: Could not load playoff schedule, using week numbers: {e}")
            # Fallback to week numbers as game types, but map to proper round names
            playoff_weeks = sorted(weekly_stats["week"].unique())
            week_to_game_type = {}
            for i, week in enumerate(playoff_weeks):
                if i == 0:
                    game_type = "WC"  # First playoff week = Wild Card
                elif i == 1:
                    game_type = "DIV"  # Second week = Divisional
                elif i == 2:
                    game_type = "CON"  # Third week = Conference Championship
                elif i == 3:
                    game_type = "SB"  # Fourth week = Super Bowl
                else:
                    game_type = f"Week_{week}"  # Any additional weeks
                week_to_game_type[week] = game_type

        # Get league scoring settings
        scoring_settings = get_league_scoring_settings(league)

        # Get drafted players
        from .models import DraftedTeam

        drafted_players = DraftedTeam.objects.filter(league=league)
        print(f"Debug: Found {drafted_players.count()} drafted players")

        # Calculate points for each player
        player_results = {}

        for drafted_player in drafted_players:
            player_id = drafted_player.gsis_id
            player_results[player_id] = {
                "player_info": {
                    "gsis_id": drafted_player.gsis_id,
                    "player_name": drafted_player.player_name,
                    "position": drafted_player.position,
                    "nfl_team": drafted_player.nfl_team,
                    "team_name": drafted_player.team_name,
                    "user": (
                        drafted_player.user.username if drafted_player.user else None
                    ),
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
                if "gsis_id" in round_stats.columns:
                    player_round_stats = round_stats[
                        round_stats["gsis_id"] == player_id
                    ]
                elif "player_id" in round_stats.columns:
                    player_round_stats = round_stats[
                        round_stats["player_id"] == player_id
                    ]
                elif "player_name" in round_stats.columns:
                    player_round_stats = round_stats[
                        round_stats["player_name"] == drafted_player.player_name
                    ]
                elif "player_display_name" in round_stats.columns:
                    player_round_stats = round_stats[
                        round_stats["player_display_name"] == drafted_player.player_name
                    ]
                else:
                    # No matching columns found, skip this round
                    continue

                # Calculate points for this round
                for _, row in player_round_stats.iterrows():
                    round_points += calculate_fantasy_points(row, scoring_settings)

                if game_type not in player_results[player_id]["round_points"]:
                    player_results[player_id]["round_points"][game_type] = 0.0

                player_results[player_id]["round_points"][game_type] += round_points
                total_points += round_points

            player_results[player_id]["total_points"] = total_points

        return player_results

    except Exception as e:
        print(f"Error in calculate_player_playoff_points: {e}")
        import traceback

        traceback.print_exc()
        return {}
