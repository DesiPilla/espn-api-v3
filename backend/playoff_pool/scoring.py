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
    # "fg_made_distance": 0,
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


def get_points_allowed_multiplier(points_allowed, scoring_dict: dict) -> float:
    """
    Get the appropriate points allowed multiplier from league scoring settings.
    Args:
        points_allowed (int/float): Points allowed by the defense
        scoring_dict: dict mapping stat names to point multipliers (should contain only one range)
    Returns:
        float: Fantasy points based on league's custom scoring for the range, or 0 if not in range
    """
    if pd.isna(points_allowed):
        return 0.0

    points_allowed = int(points_allowed)

    # Check if this points_allowed value matches any range in the scoring_dict
    for range_stat, multiplier in scoring_dict.items():
        if range_stat == "points_allowed_0" and points_allowed == 0:
            return multiplier
        elif range_stat == "points_allowed_1_6" and 1 <= points_allowed <= 6:
            return multiplier
        elif range_stat == "points_allowed_7_13" and 7 <= points_allowed <= 13:
            return multiplier
        elif range_stat == "points_allowed_14_20" and 14 <= points_allowed <= 20:
            return multiplier
        elif range_stat == "points_allowed_21_27" and 21 <= points_allowed <= 27:
            return multiplier
        elif range_stat == "points_allowed_28_34" and 28 <= points_allowed <= 34:
            return multiplier
        elif range_stat == "points_allowed_35_plus" and points_allowed >= 35:
            return multiplier

    return 0.0


def calculate_points_allowed_score(points_allowed):
    """
    DEPRECATED: Use get_points_allowed_multiplier() with league scoring settings instead.

    Calculate fantasy points based on points allowed by defense.
    This function uses hardcoded values and should no longer be used for league scoring.

    Args:
        points_allowed (int/float): Points allowed by the defense

    Returns:
        float: Fantasy points for points allowed
    """
    if pd.isna(points_allowed):
        return 0.0

    points_allowed = int(points_allowed)

    if points_allowed == 0:
        return 10.0
    elif 1 <= points_allowed <= 6:
        return 7.0
    elif 7 <= points_allowed <= 13:
        return 4.0
    elif 14 <= points_allowed <= 20:
        return 1.0
    elif 21 <= points_allowed <= 27:
        return 0.0
    elif 28 <= points_allowed <= 34:
        return -1.0
    else:  # 35+
        return -4.0


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
    # print("New week")
    # Handle points_allowed stats specially using opponent_score
    if "opponent_score" in row and not pd.isna(row["opponent_score"]):
        for stat_name in scoring_dict.keys():
            if (
                stat_name.startswith("points_allowed_")
                and stat_name != "points_allowed"
            ):
                # Get the multiplier for this specific points allowed range
                multiplier = scoring_dict[stat_name]
                if not pd.isna(multiplier):
                    points_allowed_value = get_points_allowed_multiplier(
                        row["opponent_score"], {stat_name: multiplier}
                    )
                    if points_allowed_value > 0:  # Only add if this range matches
                        # print(
                        #     "Adding stat {} with value {}".format(
                        #         stat_name, points_allowed_value
                        #     )
                        # )

                        points += points_allowed_value
                        break  # Only one range should match

    # Handle all other stats normally
    for stat, value in scoring_dict.items():
        if stat in row and not pd.isna(value) and not stat.startswith("points_allowed"):
            stat_value = row[stat]
            if pd.notna(stat_value):
                points += stat_value * value
                # if row["team"] == "PHI":
                #     print(
                #         "Adding stat {} with value {}".format(stat, stat_value * value)
                #     )

    return points
