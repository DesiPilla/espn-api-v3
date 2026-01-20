import pandas as pd
import nflreadpy as nfl
from django.core.cache import cache

from backend.playoff_pool.models import League


SCORING_MULTIPLIERS = {
    # -------------------
    # Passing
    # -------------------
    "passing_yards": {
        "display_name": "Passing Yards",
        "default_value": 1 / 25,
        "increment_value": 0.01,
        "category": "Passing",
    },
    "passing_tds": {
        "display_name": "Passing Touchdowns",
        "default_value": 4,
        "increment_value": 1,
        "category": "Passing",
    },
    "passing_interceptions": {
        "display_name": "Passing Interceptions",
        "default_value": -2,
        "increment_value": 1,
        "category": "Passing",
    },
    "sacks_suffered": {
        "display_name": "Sacks Suffered",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Passing",
    },
    "sack_fumbles_lost": {
        "display_name": "Sack Fumbles Lost",
        "default_value": -2,
        "increment_value": 1,
        "category": "Passing",
    },
    "passing_2pt_conversions": {
        "display_name": "Passing 2-Point Conversions",
        "default_value": 2,
        "increment_value": 1,
        "category": "Passing",
    },
    # -------------------
    # Rushing
    # -------------------
    "rushing_yards": {
        "display_name": "Rushing Yards",
        "default_value": 1 / 10,
        "increment_value": 0.01,
        "category": "Rushing",
    },
    "rushing_tds": {
        "display_name": "Rushing Touchdowns",
        "default_value": 6,
        "increment_value": 1,
        "category": "Rushing",
    },
    "rushing_fumbles_lost": {
        "display_name": "Rushing Fumbles Lost",
        "default_value": -2,
        "increment_value": 1,
        "category": "Rushing",
    },
    "rushing_first_downs": {
        "display_name": "Rushing First Downs",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Rushing",
    },
    "rushing_2pt_conversions": {
        "display_name": "Rushing 2-Point Conversions",
        "default_value": 2,
        "increment_value": 1,
        "category": "Rushing",
    },
    # -------------------
    # Receiving
    # -------------------
    "receptions": {
        "display_name": "Receptions (PPR)",
        "default_value": 0,  # non-PPR by default
        "increment_value": 0.5,
        "category": "Receiving",
    },
    "receiving_yards": {
        "display_name": "Receiving Yards",
        "default_value": 1 / 10,
        "increment_value": 0.01,
        "category": "Receiving",
    },
    "receiving_tds": {
        "display_name": "Receiving Touchdowns",
        "default_value": 6,
        "increment_value": 1,
        "category": "Receiving",
    },
    "receiving_fumbles_lost": {
        "display_name": "Receiving Fumbles Lost",
        "default_value": -2,
        "increment_value": 1,
        "category": "Receiving",
    },
    "receiving_first_downs": {
        "display_name": "Receiving First Downs",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Receiving",
    },
    "receiving_2pt_conversions": {
        "display_name": "Receiving 2-Point Conversions",
        "default_value": 2,
        "increment_value": 1,
        "category": "Receiving",
    },
    # -------------------
    # Kicking
    # -------------------
    "fg_made": {
        "display_name": "Field Goal Made",
        "default_value": 0,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_0_19": {
        "display_name": "Field Goal Made: 0-19 yds",
        "default_value": 3,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_20_29": {
        "display_name": "Field Goal Made: 20-29 yds",
        "default_value": 3,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_30_39": {
        "display_name": "Field Goal Made: 30-39 yds",
        "default_value": 3,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_40_49": {
        "display_name": "Field Goal Made: 40-49 yds",
        "default_value": 4,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_50_59": {
        "display_name": "Field Goal Made: 50-59 yds",
        "default_value": 5,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_60_": {
        "display_name": "Field Goal Made: 60+ yds",
        "default_value": 5,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_0_19": {
        "display_name": "Field Goal Missed: 0-19 yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_20_29": {
        "display_name": "Field Goal Missed: 20-29 yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_30_39": {
        "display_name": "Field Goal Missed: 30-39 yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_40_49": {
        "display_name": "Field Goal Missed: 40-49 yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_50_59": {
        "display_name": "Field Goal Missed: 50-59 yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_missed_60_": {
        "display_name": "Field Goal Missed: 60+ yds",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "fg_made_distance": {
        "display_name": "Field Goal Made Distance",
        "default_value": 0,
        "increment_value": 0.01,
        "category": "Kicking",
    },
    "pat_made": {
        "display_name": "PAT Made",
        "default_value": 1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "pat_missed": {
        "display_name": "PAT Missed",
        "default_value": -1,
        "increment_value": 1,
        "category": "Kicking",
    },
    "pat_blocked": {
        "display_name": "PAT Blocked",
        "default_value": 0,
        "increment_value": 1,
        "category": "Kicking",
    },
}

DEFENSE_SCORING_MULTIPLIERS = {
    # Touchdowns
    "special_teams_tds": {
        "display_name": "Special Teams Touchdowns",
        "default_value": 6,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "def_tds": {
        "display_name": "Defensive Touchdowns",
        "default_value": 6,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "fumble_recovery_tds": {
        "display_name": "Fumble Recovery Touchdowns",
        "default_value": 6,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    # Tackles (not scored in ESPN standard D/ST)
    "def_tackles_solo": {
        "display_name": "Solo Tackles",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    "def_tackles_with_assist": {
        "display_name": "Tackles With Assist",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    "def_tackle_assists": {
        "display_name": "Tackle Assists",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    "def_tackles_for_loss": {
        "display_name": "Tackles For Loss",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    "def_tackles_for_loss_yards": {
        "display_name": "Tackles For Loss Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Defense/Special Teams",
    },
    # Turnovers & pressure
    "def_fumbles_forced": {
        "display_name": "Fumbles Forced",
        "default_value": 0,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "def_fumbles": {
        "display_name": "Fumbles Recovered",
        "default_value": 2,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "def_interceptions": {
        "display_name": "Interceptions",
        "default_value": 2,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "def_interception_yards": {
        "display_name": "Interception Return Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Defense/Special Teams",
    },
    "def_sacks": {
        "display_name": "Sacks",
        "default_value": 1,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "def_sack_yards": {
        "display_name": "Sack Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Defense/Special Teams",
    },
    "def_qb_hits": {
        "display_name": "QB Hits",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    # Coverage / misc defense
    "def_pass_defended": {
        "display_name": "Passes Defended",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Defense/Special Teams",
    },
    "def_safeties": {
        "display_name": "Safeties",
        "default_value": 2,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    # Fumble recoveries (by possession)
    "fumble_recovery_own": {
        "display_name": "Own Fumble Recoveries",
        "default_value": 0,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "fumble_recovery_yards_own": {
        "display_name": "Own Fumble Recovery Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Defense/Special Teams",
    },
    "fumble_recovery_opp": {
        "display_name": "Opponent Fumble Recoveries",
        "default_value": 2,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "fumble_recovery_yards_opp": {
        "display_name": "Opponent Fumble Recovery Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Defense/Special Teams",
    },
    # Returns (yards not scored)
    "punt_returns": {
        "display_name": "Punt Returns",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Returns",
    },
    "punt_return_yards": {
        "display_name": "Punt Return Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Returns",
    },
    "kickoff_returns": {
        "display_name": "Kickoff Returns",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Returns",
    },
    "kickoff_return_yards": {
        "display_name": "Kickoff Return Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Returns",
    },
    # Misc / non-scoring
    "misc_yards": {
        "display_name": "Miscellaneous Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Miscellaneous",
    },
    "penalties": {
        "display_name": "Penalties",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Miscellaneous",
    },
    "penalty_yards": {
        "display_name": "Penalty Yards",
        "default_value": 0,
        "increment_value": 0.1,
        "category": "Miscellaneous",
    },
    "timeouts": {
        "display_name": "Timeouts",
        "default_value": 0,
        "increment_value": 0.5,
        "category": "Miscellaneous",
    },
    # Points allowed scoring
    "points_allowed": {
        "display_name": "Points Allowed",
        "default_value": 0,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    # Points allowed ranges (for custom scoring)
    "points_allowed_0": {
        "display_name": "Points Allowed: 0 Points",
        "default_value": 10,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_1_6": {
        "display_name": "Points Allowed: 1-6 Points",
        "default_value": 7,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_7_13": {
        "display_name": "Points Allowed: 7-13 Points",
        "default_value": 4,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_14_20": {
        "display_name": "Points Allowed: 14-20 Points",
        "default_value": 1,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_21_27": {
        "display_name": "Points Allowed: 21-27 Points",
        "default_value": 0,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_28_34": {
        "display_name": "Points Allowed: 28-34 Points",
        "default_value": -1,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
    "points_allowed_35_plus": {
        "display_name": "Points Allowed: 35+ Points",
        "default_value": -4,
        "increment_value": 1,
        "category": "Defense/Special Teams",
    },
}


RELEVANT_SCORING_STATS = {
    stat: config
    for stat, config in SCORING_MULTIPLIERS.items()
    if config["default_value"] != 0
}

RELEVANT_DEFENSIVE_SCORING_STATS = {
    stat: config
    for stat, config in DEFENSE_SCORING_MULTIPLIERS.items()
    if config["default_value"] != 0
    or stat == "points_allowed"  # Include points_allowed even though default is 0
}


def get_most_recent_game(year: int) -> pd.Series:
    """This function retrieves the most recent game ID for a given year.
    It can be used to identify the latest game played in that season.

    Args:
        year (int): The NFL season year.

    Returns:
        pd.Series: A pandas Series containing the game_id, gameday, and gametime
                   of the most recent game.
    """
    cache_key = f"nfl_schedule_{year}"
    schedules = cache.get(cache_key)

    if schedules is None:
        schedules = nfl.load_schedules(seasons=[year]).to_pandas()
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key, schedules, 3600)

    return (
        schedules.dropna(subset=["total", "result", "overtime"])
        .sort_values(by=["gameday", "gametime"], ascending=[False, False])
        .iloc[0][["game_id", "gameday", "gametime"]]
    )


def get_league_scoring_settings(league: League) -> dict:
    """
    Get compiled scoring settings for a league (custom + defaults).

    Args:
        league: League model instance

    Returns:
        dict: Complete scoring settings with custom overrides applied to default_value
    """
    from .models import LeagueScoringSetting

    # Start with default scoring (deep copy to avoid mutating originals)
    scoring_settings = {}
    for stat, config in {**SCORING_MULTIPLIERS, **DEFENSE_SCORING_MULTIPLIERS}.items():
        scoring_settings[stat] = config.copy()

    # Override with custom league settings (update the default_value)
    custom_settings = LeagueScoringSetting.objects.filter(league=league)
    for setting in custom_settings:
        if setting.stat_name in scoring_settings:
            scoring_settings[setting.stat_name]["default_value"] = setting.multiplier

    return scoring_settings


def calculate_fantasy_points(row: pd.Series, scoring_dict: dict) -> float:
    """
    Calculate fantasy points for a player row based on a scoring dictionary.
    Args:
        row: pandas Series representing player stats
        scoring_dict: dict mapping stat names to config dicts with default_value
    Returns:
        float: Calculated fantasy points
    """
    points = 0.0

    # print(
    #     "Calculating points for player/team:",
    #     row.get("player_name", row.get("team", "unknown")),
    # )
    for stat, config in scoring_dict.items():
        # Handle both old format (direct value) and new format (dict with default_value)
        if isinstance(config, dict):
            value = config.get("default_value", 0)
        else:
            value = config  # Backwards compatibility

        if stat in row and not pd.isna(value):
            stat_value = row[stat]
            if pd.notna(stat_value):
                points += stat_value * value
                # if row["player_name"] == "BUF D/ST":
                #     print(
                #         "Adding stat {} with value {}".format(stat, stat_value * value)
                #     )
            else:
                # print(
                #     f"Stat {stat} is NaN for team {row.get('team', 'unknown')}, skipping."
                # )
                continue
        else:
            # print(
            #     f"Stat {stat} not found in row for team {row.get('team', 'unknown')}."
            # )
            continue

    return points
