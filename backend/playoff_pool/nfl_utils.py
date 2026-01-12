"""
NFL utility functions for playoff pool application.
"""
from backend.playoff_pool.scoring import (
    calculate_fantasy_points,
    get_league_scoring_settings,
    DEFENSE_SCORING_MULTIPLIERS,
)
import nflreadpy as nfl
import pandas as pd
from django.http import JsonResponse
from django.core.cache import cache
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

        # Create cache key based on league ID and year
        cache_key = f"playoff_points_league_{league.id}_year_{year}"

        # Try to get cached result
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Cache key for NFL data (shared across all leagues for same year)
        nfl_data_cache_key = f"nfl_playoff_data_year_{year}"
        nfl_cached_data = cache.get(nfl_data_cache_key)

        if nfl_cached_data is None:
            # Get weekly stats for playoff weeks
            weekly_stats = nfl.load_player_stats([year]).to_pandas()
            weekly_stats = weekly_stats[weekly_stats["season_type"] == "POST"]

            if weekly_stats.empty:
                print(f"Debug: No playoff stats found for year {year}")
                return {}

            # Get playoff schedule to map weeks to game types
            try:
                schedule = nfl.load_schedules([year]).to_pandas()
                playoff_games = schedule[schedule["game_type"] != "REG"].copy()

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
                print(
                    f"Warning: Could not load playoff schedule, using week numbers: {e}"
                )
                # Fallback to week numbers as game types
                playoff_weeks = sorted(weekly_stats["week"].unique())
                week_to_game_type = {}
                for i, week in enumerate(playoff_weeks):
                    if i == 0:
                        game_type = "WC"
                    elif i == 1:
                        game_type = "DIV"
                    elif i == 2:
                        game_type = "CON"
                    elif i == 3:
                        game_type = "SB"
                    else:
                        game_type = f"Week_{week}"
                    week_to_game_type[week] = game_type

            # Load team stats for D/ST calculations (if needed)
            team_stats = None
            try:
                team_stats = nfl.load_team_stats(seasons=[year]).to_pandas()

                # Filter for postseason games
                if not team_stats.empty:
                    team_stats = team_stats[team_stats["season_type"] == "POST"]

                    # Further filter for playoff teams if we have the list
                    if year in PLAYOFF_TEAMS and PLAYOFF_TEAMS[year]:
                        team_stats = team_stats[
                            team_stats["team"].isin(PLAYOFF_TEAMS[year])
                        ]

                    # Add opponent scores efficiently
                    if not team_stats.empty:
                        try:
                            schedules = nfl.load_schedules(seasons=[year]).to_pandas()
                            playoff_schedules = schedules[
                                (schedules["game_type"] != "REG")
                                & (schedules["season"] == year)
                            ].copy()

                            # Create mapping for home teams (opponent score = away_score)
                            home_mapping = playoff_schedules[
                                ["season", "week", "home_team", "away_score"]
                            ].copy()
                            home_mapping.columns = [
                                "season",
                                "week",
                                "team",
                                "opponent_score",
                            ]

                            # Create mapping for away teams (opponent score = home_score)
                            away_mapping = playoff_schedules[
                                ["season", "week", "away_team", "home_score"]
                            ].copy()
                            away_mapping.columns = [
                                "season",
                                "week",
                                "team",
                                "opponent_score",
                            ]

                            # Combine both mappings
                            score_mapping = pd.concat(
                                [home_mapping, away_mapping], ignore_index=True
                            )

                            # Merge with team stats
                            team_stats = team_stats.merge(
                                score_mapping, on=["season", "week", "team"], how="left"
                            )

                            # Fill any missing opponent scores with 0
                            team_stats["opponent_score"] = team_stats[
                                "opponent_score"
                            ].fillna(0)

                            # Only keep defensive stats
                            team_stats = team_stats[
                                ["season", "week", "team", "opponent_score"]
                                + [
                                    col
                                    for col in DEFENSE_SCORING_MULTIPLIERS
                                    if col in team_stats.columns
                                ]
                            ]
                        except Exception as e:
                            print(f"Warning: Could not add opponent scores: {e}")
                            if not team_stats.empty:
                                team_stats["opponent_score"] = 0

            except Exception as e:
                print(f"Warning: Could not load team stats for D/ST: {e}")
                team_stats = None

            # Cache NFL data for 15 minutes (data doesn't change frequently during playoffs)
            nfl_cached_data = {
                "weekly_stats": weekly_stats,
                "week_to_game_type": week_to_game_type,
                "playoff_weeks": playoff_weeks,
                "team_stats": team_stats,
            }
            cache.set(nfl_data_cache_key, nfl_cached_data, 900)  # 15 minutes

        # Unpack cached NFL data
        weekly_stats = nfl_cached_data["weekly_stats"]
        week_to_game_type = nfl_cached_data["week_to_game_type"]
        playoff_weeks = nfl_cached_data.get(
            "playoff_weeks", sorted(weekly_stats["week"].unique())
        )
        team_stats = nfl_cached_data.get("team_stats", None)

        # Get league scoring settings
        scoring_settings = get_league_scoring_settings(league)

        # Get drafted players
        from .models import DraftedTeam

        drafted_players = DraftedTeam.objects.filter(league=league)

        # Separate D/ST and regular players
        dst_players = drafted_players.filter(position="DST")
        regular_players = drafted_players.exclude(position="DST")

        # Calculate points for each player
        player_results = {}

        # Process regular (non-D/ST) players
        for drafted_player in regular_players:
            player_id = drafted_player.gsis_id

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

            player_results[player_id] = {
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

        # Process D/ST players using team stats
        if dst_players.exists() and team_stats is not None and not team_stats.empty:
            for drafted_dst in dst_players:
                dst_team = drafted_dst.nfl_team  # This should be the team abbreviation
                player_id = drafted_dst.gsis_id

                # Format drafted_at in EST if available
                drafted_at_est = None
                if drafted_dst.drafted_at:
                    import pytz

                    est = pytz.timezone("America/New_York")
                    drafted_at_est = drafted_dst.drafted_at.astimezone(est).isoformat()

                # Get username from user or team_membership
                username = None
                if drafted_dst.user:
                    username = drafted_dst.user.username
                elif drafted_dst.team_membership and drafted_dst.team_membership.user:
                    username = drafted_dst.team_membership.user.username

                player_results[player_id] = {
                    "player_info": {
                        "gsis_id": drafted_dst.gsis_id,
                        "player_name": drafted_dst.player_name,
                        "position": drafted_dst.position,
                        "nfl_team": drafted_dst.nfl_team,
                        "team_name": drafted_dst.team_name,
                        "user": username,
                        "draft_order": drafted_dst.draft_order,
                        "drafted_at": (
                            drafted_dst.drafted_at.isoformat()
                            if drafted_dst.drafted_at
                            else None
                        ),
                        "drafted_at_est": drafted_at_est,
                        "id": drafted_dst.id,
                    },
                    "round_points": {},
                    "total_points": 0.0,
                }

                total_points = 0.0

                # Calculate points for each playoff round using team stats
                for week, game_type in week_to_game_type.items():
                    # Find this team's stats for this week
                    team_week_stats = team_stats[
                        (team_stats["team"] == dst_team) & (team_stats["week"] == week)
                    ]

                    round_points = 0.0

                    # Calculate points for this round using league-specific defensive scoring
                    for _, row in team_week_stats.iterrows():
                        round_points += calculate_fantasy_points(row, scoring_settings)

                    if game_type not in player_results[player_id]["round_points"]:
                        player_results[player_id]["round_points"][game_type] = 0.0

                    player_results[player_id]["round_points"][game_type] += round_points
                    total_points += round_points

                player_results[player_id]["total_points"] = total_points
        elif dst_players.exists():
            print(
                f"Warning: Found {dst_players.count()} D/ST players but no team stats available"
            )
            # Still create entries for D/ST players with 0 points
            for drafted_dst in dst_players:
                player_id = drafted_dst.gsis_id
                player_results[player_id] = {
                    "player_info": {
                        "gsis_id": drafted_dst.gsis_id,
                        "player_name": drafted_dst.player_name,
                        "position": drafted_dst.position,
                        "nfl_team": drafted_dst.nfl_team,
                        "team_name": drafted_dst.team_name,
                        "user": (
                            drafted_dst.user.username if drafted_dst.user else None
                        ),
                    },
                    "round_points": {},
                    "total_points": 0.0,
                }

        # Cache the calculated result for 5 minutes
        cache.set(cache_key, player_results, 300)

        return player_results

    except Exception as e:
        print(f"Error in calculate_player_playoff_points: {e}")
        import traceback

        traceback.print_exc()
        return {}
