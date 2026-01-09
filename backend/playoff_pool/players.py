from typing import List

import nflreadpy as nfl
import pandas as pd
import polars as pl

from backend.playoff_pool.scoring import (
    RELEVANT_SCORING_STATS,
    RELEVANT_DEFENSIVE_SCORING_STATS,
    calculate_fantasy_points,
)
from backend.playoff_pool.models import PlayoffDraftablePlayer

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


def get_all_playoff_players(
    year: int, positions_to_keep: List[str] = ["QB", "RB", "WR", "TE", "K", "DST"]
) -> pd.DataFrame:

    # ------------ Get list of individual players ------------
    # Load rosters for the playoff teams
    playoff_rosters = nfl.load_rosters([year]).to_pandas()
    playoff_rosters = playoff_rosters[playoff_rosters["team"].isin(PLAYOFF_TEAMS[year])]

    # Load player game-level stats for multiple seasons
    player_stats = nfl.load_player_stats([year]).to_pandas()
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
    # Load all available team level stats
    team_stats = nfl.load_team_stats(seasons=[year]).to_pandas()

    playoff_team_stats = team_stats[
        team_stats["team"].isin(PLAYOFF_TEAMS[year])
        & (team_stats["season_type"] == "REG")
    ]

    playoff_team_stats["fantasy_points"] = playoff_team_stats.apply(
        lambda row: calculate_fantasy_points(row, RELEVANT_DEFENSIVE_SCORING_STATS),
        axis=1,
    )

    playoff_dst_stats = (
        playoff_team_stats.groupby("team")[["fantasy_points"]].sum().reset_index()
    )
    playoff_dst_stats["gsis_id"] = playoff_dst_stats["team"]
    playoff_dst_stats["full_name"] = playoff_dst_stats["team"] + " D/ST"
    playoff_dst_stats["position"] = "DST"
    playoff_dst_stats["player_id"] = playoff_dst_stats["gsis_id"]

    # Combine skill players and DSTs
    playoff_players = pd.concat([playoff_skill_players, playoff_dst_stats])

    # Filter by positions to keep
    playoff_players_filtered = playoff_players[
        playoff_players["position"].isin(positions_to_keep)
    ]

    return playoff_players_filtered[
        ["gsis_id", "player_id", "full_name", "team", "position", "fantasy_points"]
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
            "gsis_id", "player_id", "full_name", "team", "position", "fantasy_points"
        )
    )
