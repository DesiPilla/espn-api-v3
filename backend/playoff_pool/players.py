from typing import List

import nflreadpy as nfl
import pandas as pd
import polars as pl

from backend.playoff_pool.scoring import (
    RELEVANT_SCORING_STATS,
    RELEVANT_DEFENSIVE_SCORING_STATS,
    calculate_fantasy_points,
)


def get_all_playoff_players(
    year: int, positions_to_keep: List[str] = ["QB", "RB", "WR", "TE", "K", "DST"]
) -> pd.DataFrame:
    # Load the schedules for the given year
    nfl_schedule = nfl.load_schedules(year)

    # Get the game IDs for all playoff games
    playoff_game_ids = nfl_schedule.filter(pl.col("game_type") != "REG")[
        "game_id"
    ].to_list()

    # Get the unique playoff teams from the game IDs
    playoff_teams = set(
        [
            team
            for gid in playoff_game_ids
            for team in (gid.split("_")[-2], gid.split("_")[-1])
        ]
    )

    # ------------ Get list of individual players ------------
    # Load rosters for the playoff teams
    playoff_rosters = nfl.load_rosters([year]).to_pandas()
    playoff_rosters = playoff_rosters[playoff_rosters["team"].isin(playoff_teams)]
    
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
        team_stats["team"].isin(playoff_teams) & (team_stats["season_type"] == "REG")
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

    return playoff_players_filtered
