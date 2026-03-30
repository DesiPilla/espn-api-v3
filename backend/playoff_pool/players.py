from typing import List

import nflreadpy as nfl
import pandas as pd
from django.core.cache import cache

from backend.playoff_pool.scoring import (
    DEFENSE_SCORING_MULTIPLIERS,
    RELEVANT_SCORING_STATS,
    RELEVANT_DEFENSIVE_SCORING_STATS,
    calculate_fantasy_points,
)
from backend.playoff_pool.models import PlayoffDraftablePlayer

CACHE_DURATION = 2 * 60
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
    2025: [
        "DEN",
        "NE",
        "JAX",
        "PIT",
        "HOU",
        "BUF",
        "LAC",
        "SEA",
        "CHI",
        "PHI",
        "CAR",
        "LA",  # Rams are encoded as "LA" in nflreadpy
        "SF",
        "GB",
    ],
}


def load_raw_schedule(year: int) -> pd.DataFrame:
    """Load and cache the raw NFL schedule DataFrame for the given year.

    Args:
        year (int): NFL season year
    Returns:
        pd.DataFrame: Raw schedule DataFrame as returned by nflreadpy
    """
    cache_key = f"nfl_schedule_{year}"
    schedule = cache.get(cache_key)

    if schedule is None:
        schedule = nfl.load_schedules(seasons=[year]).to_pandas()
        cache.set(cache_key, schedule, timeout=CACHE_DURATION)

    return schedule


def get_schedule(year: int) -> pd.DataFrame:
    """Load NFL schedule for the given year with caching.

    Args:
        year (int): NFL season year
    Returns:
        pd.DataFrame: DataFrame of the NFL schedule for the given year
    """
    schedule = load_raw_schedule(year)

    # Create mapping for home teams (opponent score = away_score)
    home_mapping = (
        schedule[["season", "week", "home_team", "home_score", "away_score"]]
        .copy()
        .rename(
            columns={
                "home_team": "team",
                "home_score": "team_score",
                "away_score": "opponent_score",
            }
        )
    )

    # Create mapping for away teams (opponent score = home_score)
    away_mapping = (
        schedule[["season", "week", "away_team", "home_score", "away_score"]]
        .copy()
        .rename(
            columns={
                "away_team": "team",
                "away_score": "team_score",
                "home_score": "opponent_score",
            }
        )
    )

    # Combine both mappings
    score_mapping = pd.concat([home_mapping, away_mapping], ignore_index=True)
    return score_mapping


def get_defense_stats(year: int) -> pd.DataFrame:
    """Because defensive stats are team stats, they are not returned
    by the nfl.load_stats() method. This function handles all defense
    stat loading so that the dataframe exists out of the box.

    Args:
        year (int): NFL season year

    Returns:
        pd.DataFrame: DataFrame of defensive stats for all teams
    """

    # Load all available team level stats (with caching)
    cache_key = f"nfl_team_stats_{year}"
    defense_stats = cache.get(cache_key)

    if defense_stats is None:
        defense_stats = nfl.load_team_stats(seasons=[year]).to_pandas()
        cache.set(cache_key, defense_stats, timeout=CACHE_DURATION)

    # Add team D/ST identifiers
    defense_stats["gsis_id"] = defense_stats["team"]
    defense_stats["full_name"] = defense_stats["team"] + " D/ST"
    defense_stats["position"] = "DST"
    defense_stats["player_id"] = defense_stats["gsis_id"]

    # Keep only relevant columns
    defense_stats = defense_stats[
        [
            "season",
            "week",
            "gsis_id",
            "full_name",
            "position",
            "player_id",
            "team",
            "season_type",
        ]
        + [
            key
            for key in DEFENSE_SCORING_MULTIPLIERS.keys()
            if key in defense_stats.columns
        ]
    ]

    # Merge with team stats
    score_mapping = get_schedule(year).rename(
        columns={"opponent_score": "points_allowed"}
    )
    defense_stats = defense_stats.merge(
        score_mapping, on=["season", "week", "team"], how="left"
    )

    # Calculate points allowed ranges, since it is used in scoring but not provided directly
    points_allowed_ranges = [
        key for key in DEFENSE_SCORING_MULTIPLIERS.keys() if "points_allowed_" in key
    ]

    for pa_range in points_allowed_ranges:
        # Extract the min and max from the key name
        min_max = pa_range.replace("points_allowed_", "").split("_")

        if min_max[0] == "0":
            defense_stats[pa_range] = (defense_stats["points_allowed"] == 0).astype(int)
        elif min_max[1] == "plus":
            defense_stats[pa_range] = (
                defense_stats["points_allowed"] >= int(min_max[0])
            ).astype(int)
        else:
            defense_stats[pa_range] = (
                (defense_stats["points_allowed"] >= int(min_max[0]))
                & (defense_stats["points_allowed"] <= int(min_max[1]))
            ).astype(int)

    return defense_stats


def add_draft_value(df, positions, league_size=12):
    """
    Add a draft_value column to a fantasy football DataFrame using
    Value Over Replacement Player (VORP).

    This function:
    - Dynamically builds replacement ranks for all positions
    - Accounts for positional scarcity (RB/WR/TE/IDP/etc.)
    - Safely handles non-fantasy positions (OL, LS, P, etc.)
    - Produces realistic draft ordering without hardcoding position weights

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain:
        - 'position'
        - 'fantasy_points'

    positions : list[str]
        List of all possible position labels in the dataset

    league_size : int, default=12
        Number of teams in the league

    Returns
    -------
    pandas.DataFrame
        Copy of df with an added 'draft_value' column
    """

    # ------------------------------------------------------------------
    # Position aliases: map granular NFL positions to fantasy families
    # ------------------------------------------------------------------
    POSITION_ALIASES = {
        # Offensive line
        "C": "OL",
        "G": "OL",
        "OT": "OL",
        # Linebackers
        "ILB": "LB",
        "OLB": "LB",
        "MLB": "LB",
        # Defensive line
        "DE": "DL",
        "DT": "DL",
        "NT": "DL",
        # Secondary
        "CB": "DB",
        "S": "DB",
        "FS": "DB",
        "SAF": "DB",
    }

    # ------------------------------------------------------------------
    # Replacement rank logic by position.
    # Each lambda returns how deep into the position pool a player must be
    # before they are considered "replacement level", given league size (n).
    #
    # Deeper replacement ranks indicate higher positional scarcity.
    # RB/WR are pushed deepest due to multiple starters, FLEX usage,
    # injury risk, and bench hoarding. QB/TE get modest buffers.
    # K and DST are fully streamable and use the starter cutoff.

    # ------------------------------------------------------------------
    CORE_REPLACEMENT_RULES = {
        # Offense
        "QB": lambda n: n,
        "RB": lambda n: n * 2 + 6,
        "WR": lambda n: n * 2 + 6,
        "TE": lambda n: n + 3,
        "K": lambda n: n,
        "DST": lambda n: n,
        # IDP (generic assumptions: ~2 starters per team)
        "LB": lambda n: n * 2,
        "DL": lambda n: n * 2,
        "DB": lambda n: n * 2,
    }

    def default_replacement_rank(_):
        """
        Replacement rank for positions not used in fantasy lineups.
        These collapse naturally to ~0 draft value.
        """
        return 1

    # ------------------------------------------------------------------
    # Build replacement rank for every position in the dataset
    # ------------------------------------------------------------------
    def build_replacement_rank():
        replacement_rank = {}

        for pos in positions:
            base_pos = POSITION_ALIASES.get(pos, pos)

            if base_pos in CORE_REPLACEMENT_RULES:
                replacement_rank[pos] = CORE_REPLACEMENT_RULES[base_pos](league_size)
            else:
                replacement_rank[pos] = default_replacement_rank(league_size)

        return replacement_rank

    REPLACEMENT_RANK = build_replacement_rank()

    # ------------------------------------------------------------------
    # Compute replacement-level fantasy points by position
    # ------------------------------------------------------------------
    def compute_replacement_points():
        replacement_points = {}

        for pos, rank in REPLACEMENT_RANK.items():
            pos_df = df[df["position"] == pos].sort_values(
                "fantasy_points", ascending=False
            )

            if len(pos_df) >= rank:
                replacement_points[pos] = pos_df.iloc[rank - 1]["fantasy_points"]
            else:
                replacement_points[pos] = 0

        return replacement_points

    replacement_points = compute_replacement_points()

    # ------------------------------------------------------------------
    # Compute draft value (VORP)
    # ------------------------------------------------------------------
    result = df.copy()

    result["draft_value"] = result.apply(
        lambda r: r["fantasy_points"] - replacement_points.get(r["position"], 0),
        axis=1,
    )

    # Players below replacement level have zero draft value
    result["draft_value"] = result["draft_value"].clip(lower=0)

    # Scale draft value to a 0-100 range
    result["draft_value"] = (result["draft_value"] / result["draft_value"].max()) * 100

    return result


def get_all_playoff_players(
    year: int, positions_to_keep: List[str] = ["QB", "RB", "WR", "TE", "K", "DST"]
) -> pd.DataFrame:
    # ------------ Get list of individual players ------------
    # Load rosters for the playoff teams (with caching)
    cache_key_rosters = f"nfl_rosters_{year}"
    playoff_rosters = cache.get(cache_key_rosters)

    if playoff_rosters is None:
        playoff_rosters = nfl.load_rosters([year]).to_pandas()
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key_rosters, playoff_rosters, timeout=CACHE_DURATION)

    playoff_rosters = playoff_rosters[playoff_rosters["team"].isin(PLAYOFF_TEAMS[year])]

    # Load player game-level stats for multiple seasons (with caching)
    cache_key_stats = f"nfl_player_stats_{year}"
    player_stats = cache.get(cache_key_stats)

    if player_stats is None:
        player_stats = nfl.load_player_stats([year]).to_pandas()
        # Cache for 1 hour (3600 seconds)
        cache.set(cache_key_stats, player_stats, timeout=CACHE_DURATION)
    player_stats["fantasy_points"] = player_stats.apply(
        lambda row: calculate_fantasy_points(row, RELEVANT_SCORING_STATS),
        axis=1,
    )

    # Get the total fantasy points for each player in the playoff rosters
    playoff_skill_players = (
        pd.merge(
            playoff_rosters,
            player_stats.groupby("player_id", as_index=False).sum(numeric_only=True)[
                ["player_id", "fantasy_points"]
            ],
            left_on="gsis_id",
            right_on="player_id",
            how="left",
        )
        .fillna(0)
        .sort_values(["position", "fantasy_points"], ascending=[True, False])
    )

    # ------------ Get list of Defenses ------------
    defense_stats = get_defense_stats(year)
    defense_stats = defense_stats[
        defense_stats["team"].isin(PLAYOFF_TEAMS[year])
        & (defense_stats["season_type"] == "REG")
    ]

    defense_stats["fantasy_points"] = defense_stats.apply(
        lambda row: calculate_fantasy_points(row, RELEVANT_DEFENSIVE_SCORING_STATS),
        axis=1,
    )

    playoff_dst_stats = (
        defense_stats.groupby("team")[["fantasy_points"]].sum().reset_index()
    )

    # Combine skill players and DSTs
    playoff_players = pd.concat([playoff_skill_players, playoff_dst_stats])

    # Filter by positions to keep
    playoff_players_filtered = playoff_players[
        playoff_players["position"].isin(positions_to_keep)
    ]

    # Add draft value
    playoff_players_filtered = add_draft_value(
        df=playoff_players_filtered, positions=positions_to_keep
    )

    return playoff_players_filtered[
        [
            "gsis_id",
            "player_id",
            "full_name",
            "team",
            "position",
            "fantasy_points",
            "draft_value",
        ]
    ]


def upload_playoff_players_to_db(
    year: int, positions_to_keep=["QB", "RB", "WR", "TE", "K", "DST"]
):
    """
    Uploads the output of get_all_playoff_players() to the PlayoffDraftablePlayer table for the given year.
    Overwrites existing records for that year.
    """
    df = get_all_playoff_players(year, positions_to_keep)
    # Remove existing records for this year
    PlayoffDraftablePlayer.objects.filter(year=year).delete()
    # Bulk create new records
    players = [
        PlayoffDraftablePlayer(
            year=year,
            gsis_id=row["gsis_id"],
            player_id=row["player_id"],
            full_name=row["full_name"],
            team=row["team"],
            position=row["position"],
            fantasy_points=row["fantasy_points"],
            draft_value=row["draft_value"],
        )
        for _, row in df.iterrows()
    ]
    PlayoffDraftablePlayer.objects.bulk_create(players)
    return len(players)


def query_playoff_players_from_db(
    year: int, positions_to_keep=["QB", "RB", "WR", "TE", "K", "DST"]
):
    """
    Query playoff players from the PlayoffDraftablePlayer table for the given year and positions.
    Returns a list of dicts matching the original get_all_playoff_players() output.
    """
    qs = PlayoffDraftablePlayer.objects.filter(
        year=year, position__in=positions_to_keep
    )
    return list(
        qs.values(
            "gsis_id",
            "player_id",
            "full_name",
            "team",
            "position",
            "fantasy_points",
            "draft_value",
        )
    )
