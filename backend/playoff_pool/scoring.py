import pandas as pd

from backend.playoff_pool.models import League


SCORING_MULTIPLIERS = {
    # -------------------
    # Passing
    # -------------------
    # "completions": 0,
    # "attempts": 0,
    "passing_yards": 1 / 25,
    "passing_tds": 4,
    "passing_interceptions": -2,
    "sacks_suffered": 0,
    # "sack_yards_lost": 0,
    # "sack_fumbles": 0,
    "sack_fumbles_lost": -2,
    # "passing_air_yards": 0,
    # "passing_yards_after_catch": 0,
    # "passing_first_downs": 0,
    # "passing_epa": 0,
    # "passing_cpoe": 0,
    "passing_2pt_conversions": 2,
    # "pacr": 0,
    # -------------------
    # Rushing
    # -------------------
    # "carries": 0,
    "rushing_yards": 1 / 10,
    "rushing_tds": 6,
    # "rushing_fumbles": 0,
    "rushing_fumbles_lost": -2,
    "rushing_first_downs": 0,
    # "rushing_epa": 0,
    "rushing_2pt_conversions": 2,
    # -------------------
    # Receiving
    # -------------------
    "receptions": 0,  # non-PPR
    # "targets": 0,
    "receiving_yards": 1 / 10,
    "receiving_tds": 6,
    # "receiving_fumbles": 0,
    "receiving_fumbles_lost": -2,
    # "receiving_air_yards": 0,
    # "receiving_yards_after_catch": 0,
    "receiving_first_downs": 0,
    # "receiving_epa": 0,
    "receiving_2pt_conversions": 2,
    # "racr": 0,
    # "target_share": 0,
    # "air_yards_share": 0,
    # "wopr": 0,
    # -------------------
    # Defense / IDP
    # -------------------
    # "special_teams_tds": 6,
    # "def_tackles_solo": 1,
    # "def_tackles_with_assist": 0,
    # "def_tackle_assists": 0.5,
    # "def_tackles_for_loss": 1,
    # "def_tackles_for_loss_yards": 0,
    # "def_fumbles_forced": 2,
    # "def_sacks": 2,
    # "def_sack_yards": 0,
    # "def_qb_hits": 0,
    # "def_interceptions": 2,
    # "def_interception_yards": 0,
    # "def_pass_defended": 1,
    # "def_tds": 6,
    # "def_fumbles": 2,  # recovered
    # "def_safeties": 2,
    # -------------------
    # Fumble recoveries
    # -------------------
    # "fumble_recovery_own": 0,
    # "fumble_recovery_yards_own": 0,
    # "fumble_recovery_opp": 2,
    # "fumble_recovery_yards_opp": 0,
    # "fumble_recovery_tds": 6,
    # -------------------
    # Returns / misc
    # -------------------
    # "misc_yards": 0,
    # "penalties": 0,
    # "penalty_yards": 0,
    # "punt_returns": 0,
    # "punt_return_yards": 0,
    # "kickoff_returns": 0,
    # "kickoff_return_yards": 0,
    # -------------------
    # Kicking
    # -------------------
    "fg_made": 0,
    # "fg_att": 0,
    # "fg_missed": -1,
    # "fg_blocked": 0,
    # "fg_long": 0,
    # "fg_pct": 0,
    "fg_made_0_19": 3,
    "fg_made_20_29": 3,
    "fg_made_30_39": 3,
    "fg_made_40_49": 4,
    "fg_made_50_59": 5,
    "fg_made_60_": 5,
    "fg_missed_0_19": -1,
    "fg_missed_20_29": -1,
    "fg_missed_30_39": -1,
    "fg_missed_40_49": -1,
    "fg_missed_50_59": -1,
    "fg_missed_60_": -1,
    # "fg_made_list": 0, # Lists will break the calculation
    # "fg_missed_list": 0, # Lists will break the calculation
    # "fg_blocked_list": 0, # Lists will break the calculation
    "fg_made_distance": 0,
    # "fg_missed_distance": 0,
    # "fg_blocked_distance": 0,
    "pat_made": 1,
    # "pat_att": 0,
    "pat_missed": -1,
    "pat_blocked": 0,
    # "pat_pct": 0,
    # "gwfg_made": 0,
    # "gwfg_att": 0,
    # "gwfg_missed": 0,
    # "gwfg_blocked": 0,
    # "gwfg_distance": 0,
}

DEFENSE_SCORING_MULTIPLIERS = {
    # Touchdowns
    "special_teams_tds": 6,
    "def_tds": 6,
    "fumble_recovery_tds": 6,
    # Tackles (not scored in ESPN standard D/ST)
    "def_tackles_solo": 0,
    "def_tackles_with_assist": 0,
    "def_tackle_assists": 0,
    "def_tackles_for_loss": 0,
    "def_tackles_for_loss_yards": 0,
    # Turnovers & pressure
    "def_fumbles_forced": 0,  # ESPN only scores fumble recoveries
    "def_fumbles": 2,  # fumbles recovered
    "def_interceptions": 2,
    "def_interception_yards": 0,
    "def_sacks": 1,
    "def_sack_yards": 0,
    "def_qb_hits": 0,
    # Coverage / misc defense
    "def_pass_defended": 0,
    "def_safeties": 2,
    # Fumble recoveries (by possession)
    "fumble_recovery_own": 0,
    "fumble_recovery_yards_own": 0,
    "fumble_recovery_opp": 2,
    "fumble_recovery_yards_opp": 0,
    # Returns (yards not scored)
    "punt_returns": 0,
    "punt_return_yards": 0,
    "kickoff_returns": 0,
    "kickoff_return_yards": 0,
    # Misc / non-scoring
    "misc_yards": 0,
    "penalties": 0,
    "penalty_yards": 0,
    "timeouts": 0,
    # Points allowed scoring
    "points_allowed": 0,  # This will be calculated dynamically
    # Points allowed ranges (for custom scoring)
    "points_allowed_0": 10,
    "points_allowed_1_6": 7,
    "points_allowed_7_13": 4,
    "points_allowed_14_20": 1,
    "points_allowed_21_27": 0,
    "points_allowed_28_34": -1,
    "points_allowed_35_plus": -4,
}


RELEVANT_SCORING_STATS = {
    stat: multiplier for stat, multiplier in SCORING_MULTIPLIERS.items() if multiplier != 0
}

RELEVANT_DEFENSIVE_SCORING_STATS = {
    stat: multiplier
    for stat, multiplier in DEFENSE_SCORING_MULTIPLIERS.items()
    if multiplier != 0
    or stat == "points_allowed"  # Include points_allowed even though multiplier is 0
}


def get_league_scoring_settings(league: League) -> dict:
    """
    Get compiled scoring settings for a league (custom + defaults).

    Args:
        league: League model instance

    Returns:
        dict: Complete scoring settings with custom overrides
    """
    from .models import LeagueScoringSetting

    # Start with default scoring
    scoring_settings = {**SCORING_MULTIPLIERS, **DEFENSE_SCORING_MULTIPLIERS}

    # Override with custom league settings
    custom_settings = LeagueScoringSetting.objects.filter(league=league)
    for setting in custom_settings:
        scoring_settings[setting.stat_name] = setting.multiplier

    return scoring_settings


def calculate_fantasy_points(row: pd.Series, scoring_dict: dict) -> float:
    """
    Calculate fantasy points for a player row based on a scoring dictionary.
    Args:
        row: pandas Series representing player stats
        scoring_dict: dict mapping stat names to point multipliers
    Returns:
        float: Calculated fantasy points
    """
    points = 0.0

    # print(
    #     "Calculating points for player/team:",
    #     row.get("player_name", row.get("team", "unknown")),
    # )
    for stat, value in scoring_dict.items():
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
