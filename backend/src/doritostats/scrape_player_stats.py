import logging
from typing import List

import pandas as pd
from espn_api.football import League, Team, Player
from backend.src.doritostats.fetch_utils import fetch_league

logger = logging.getLogger(__name__)


def extract_player_stats(
    team: Team, team_lineup: List[Player], week: int
) -> pd.DataFrame:
    df = pd.DataFrame()
    for i, player in enumerate(team_lineup):
        player_data = {
            "week": week,
            "team_owner": team.owner,
            "team_name": team.team_name,
            "team_division": team.division_name,
            "player_name": player.name,
            "player_id": player.playerId,
            "position_rank": player.posRank,  # Empty?
            "eligible_slots": player.eligibleSlots,
            "acquisition_type": player.acquisitionType,  # Empty?
            "pro_team": player.proTeam,
            "current_team_id": player.onTeamId,  # The current ESPN fantasy team ID that the player is on (only accurate at time of query)
            "player_position": player.position,
            "player_active_status": player.active_status,
            "stats": player.stats,
        }

        # Add stat to player_data
        if week in player.stats.keys() and player.active_status != "bye":
            player_data["player_points_week"] = player.stats[week]["points"]
            player_data["player_percent_owned"] = player.percent_owned
            player_data["player_percent_started"] = player.percent_started
            player_data["player_total_points"] = player.total_points
            player_data["player_projected_total_points"] = player.projected_total_points
            player_data["player_avg_points"] = player.avg_points
            player_data["player_projected_avg_points"] = player.projected_avg_points
        else:
            player_data["player_points_week"] = 0
            player_data["player_percent_owned"] = 0
            player_data["player_percent_started"] = 0
            player_data["player_total_points"] = 0
            player_data["player_projected_total_points"] = 0
            player_data["player_avg_points"] = 0
            player_data["player_projected_avg_points"] = 0

        if 0 in player.stats.keys():
            player_data["player_points_season"] = player.stats[0]["points"]
        else:
            player_data["player_points_season"] = 0

        df = pd.concat([df, pd.Series(player_data).to_frame().T])

    return df


def get_stats_by_matchup(
    league_id: int, year: int, swid: str, espn_s2: str
) -> pd.DataFrame:
    """This function creates a historical dataframe for the league in a given year.
    The data is based on player-level stats, and is organized by week and matchup.

    It generates this dataframe by:
        - For each week that has elapsed, get the BoxScores for that week:
            - For each Matchup in the BoxScores:
                Grab each stat by looking at the Matchup.home_team, Matchup.home_lineup, Matchup.away_team, and Matchup.away_lineup

    This is used for years in 2019 or later, where the BoxScores are available.

    Args:
        league_id (int): League ID
        year (int): Year of the league
        swid (str): User credential
        espn_s2 (str): User credential

    Returns:
        pd.DataFrame: Historical player stats dataframe
    """
    # Fetch league for year
    league = fetch_league(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)

    # Instantiate data frame
    df = pd.DataFrame()

    # Loop through each week that has happened
    current_matchup_period = league.settings.week_to_matchup_period[league.current_week]
    for week in range(current_matchup_period):
        league.load_roster_week(week + 1)
        box_scores = league.box_scores(week + 1)

        # Instantiate week data frame
        df_week = pd.DataFrame()
        for i, matchup in enumerate(box_scores):
            # Skip byes
            if (type(matchup.home_team) != Team) or (type(matchup.away_team) != Team):
                continue

            # Get stats for home team
            df_home_team = extract_player_stats(
                matchup.home_team, matchup.home_lineup, week + 1
            )

            # Get stats for away team
            df_away_team = extract_player_stats(
                matchup.away_team, matchup.away_lineup, week + 1
            )

            # Append to week data frame
            df_week = pd.concat([df_week, df_home_team, df_away_team])

        df = pd.concat([df, df_week])

    df["league_id"] = league_id
    df["year"] = year

    return df
