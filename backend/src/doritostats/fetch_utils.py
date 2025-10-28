import datetime
import logging
import os
import re
import requests
import warnings
from contextlib import contextmanager
from typing import Optional, Tuple

import pandas as pd
import sqlalchemy
from dotenv import load_dotenv
from espn_api.football import League
from espn_api.requests.constant import FANTASY_BASE_ENDPOINT
from espn_api.requests.espn_requests import ESPNInvalidLeague, ESPNUnknownError

# TEMPORARY IMPORTS
from espn_api.football import Team
from espn_api.football.helper import (
    sort_team_data_list,
    sort_by_division_record,
    sort_by_head_to_head,
    sort_by_win_pct,
    sort_by_points_for,
    sort_by_points_against,
    sort_by_coin_flip,
)
from typing import List

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

OWNER_MAP = {
    "Katie Brooks": "Nikki Pilla",
    "Joseph Ricupero": "Jojo & Matt",
    "Marc C": "Marco Chirico",
    "Marc Chirico": "Marco Chirico",
}


@contextmanager
def get_postgres_conn() -> sqlalchemy.engine.base.Connection:
    """Create a postrges connection using the DATABASE_URL environment variable.

    Returns:
        sqlalchemy.engine.base.Connection: A connection to the database.
    """
    # Load environment variables
    load_dotenv("../.env", override=True)

    # Create a connection to the database
    conn_str = os.path.expandvars(os.environ.get("DATABASE_URL")).replace(
        "postgres://", "postgresql://"
    )
    engine = sqlalchemy.create_engine(conn_str, pool_pre_ping=True)
    conn = engine.connect()
    try:
        yield conn
    finally:
        conn.close()
        engine.dispose()


def get_league_creds(
    league_id: int, year: Optional[int] = None
) -> Tuple[int, int, int, int]:
    """Retrieves league credentials for a specified league ID and optional year from the database.

    Queries the `fantasy_stats_leagueinfo` table for the given `league_id` and, if provided, the specified `year`.
    Returns the most recent league credentials if multiple entries exist.

        league_id (int): The unique identifier for the league.
        year (Optional[int], optional): The year of the league season. If not provided, retrieves the most recent entry.

    Returns:
        Tuple[int, int, int, int]: A tuple containing:
            - league_id (int): The league's unique identifier.
            - league_year (int): The year of the league season.
            - swid (int): The SWID credential for the league.
            - espn_s2 (int): The ESPN S2 credential for the league.

    Raises:
        Exception: If no credentials are found for the given league_id and year.
    league_id: int, year: Optional[int] = None
    """
    with get_postgres_conn() as conn:
        # Query all the league info data
        sql = f"""
        SELECT league_id, league_year, swid, espn_s2
        FROM public.fantasy_stats_leagueinfo
        WHERE league_id = {league_id}
        """
        if year:
            sql += f" AND league_year = {year}"
        league_info_df = pd.read_sql(sql, conn)

    if league_info_df.empty:
        raise Exception(
            "No league credentials found for league_id {} and year {}".format(
                league_id, year
            )
        )
    league_id, league_year, swid, espn_s2 = (
        league_info_df.sort_values(by="league_year", ascending=False).iloc[0].values
    )
    return league_id, league_year, swid, espn_s2


def set_league_endpoint(league: League) -> None:
    """Set the league's endpoint."""

    # "This" year is considered anything after June
    now = datetime.datetime.today()
    if now.month > 6:
        current_year = now.year
    else:
        current_year = now.year - 1

    # Current season
    if league.year >= current_year:
        league.endpoint = f"{FANTASY_BASE_ENDPOINT}ffl/seasons/{league.year}/segments/0/leagues/{league.league_id}?"

    # Old season
    else:
        league.endpoint = f"{FANTASY_BASE_ENDPOINT}ffl/leagueHistory/{league.league_id}?seasonId={league.year}&"
    print(f"LOGGER NAME: {logger.name}")

    print("[BUILDING LEAGUE] League endpoint set to: {}".format(league.endpoint))


def verify_league_is_active(league: League) -> None:
    """Verify that the league is active and not in the offseason.

    Args:
        league (League): ESPN League object
    """
    # Check if the league is active
    r = requests.get(league.endpoint, cookies=league.cookies).json()

    if type(r) == list:
        r = r[0]

    # Check if the league is active
    if (r.get("status") is not None) and (r.get("status").get("isActive")):
        print("[BUILDING LEAGUE] League is active.")
    elif (r.get("status") is not None) and (not r.get("status").get("isActive")):
        print("[BUILDING LEAGUE] League is either not active.")
        raise Exception(
            "League {} is not active. The league must be activated on ESPN to use.".format(
                league.league_id
            )
        )
    # Check if r has a key called "messages" and if that value is "Not Found"
    elif r.get("messages") is not None:
        if r["messages"] == ["Not Found"]:
            print("[BUILDING LEAGUE] League was not found.")
            raise ESPNInvalidLeague(
                "League {} was not found. Please check that the credentials are valid.".format(
                    league.league_id
                )
            )
        else:
            print("[BUILDING LEAGUE] League endpoint does not work. Error unknown.")
            raise ESPNUnknownError(
                "An error has occurred fetching league {}.".format(league.league_id)
            )
    else:
        print("[BUILDING LEAGUE] League endpoint does not work. Error unknown.")
        raise ESPNUnknownError(
            "An error has occurred fetching league {}.".format(league.league_id)
        )


def get_roster_settings(league: League) -> None:
    """This grabs the roster and starting lineup settings for the league
    - Grabs the dictionary containing the number of players of each position a roster contains
    - Creates a dictionary roster_slots{} that only inlcludes slotIds that have a non-zero number of players on the roster
    - Creates a dictionary starting_roster_slots{} that is a subset of roster_slots{} and only includes slotIds that are on the starting roster
    - Add roster_slots{} and starting_roster_slots{} to the League attribute League.rosterSettings
    """
    print("[BUILDING LEAGUE] Gathering roster settings information...")

    # This dictionary maps each slotId to the position it represents
    rosterMap = {
        0: "QB",
        1: "TQB",
        2: "RB",
        3: "RB/WR",
        4: "WR",
        5: "WR/TE",
        6: "TE",
        7: "OP",
        8: "DT",
        9: "DE",
        10: "LB",
        11: "DL",
        12: "CB",
        13: "S",
        14: "DB",
        15: "DP",
        16: "D/ST",
        17: "K",
        18: "P",
        19: "HC",
        20: "BE",
        21: "IR",
        22: "",
        23: "RB/WR/TE",
        24: " ",
    }

    endpoint = "{}view=mMatchupScore&view=mTeam&view=mSettings".format(league.endpoint)
    r = requests.get(endpoint, cookies=league.cookies).json()
    if type(r) == list:
        r = r[0]
    settings = r["settings"]

    league.name = settings["name"]
    league.is_season_complete = r["schedule"][-1]["winner"] != "UNDECIDED"

    # Grab the dictionary containing the number of players of each position a roster contains
    roster = settings["rosterSettings"]["lineupSlotCounts"]
    # Create an empty dictionary that will replace roster{}
    roster_slots = {}
    # Create an empty dictionary that will be a subset of roster_slots{} containing only starting players
    starting_roster_slots = {}
    for positionId in roster:
        position = rosterMap[int(positionId)]
        # Only inlclude slotIds that have a non-zero number of players on the roster
        if roster[positionId] != 0:
            roster_slots[position] = roster[positionId]
            # Include all slotIds in the starting_roster_slots{} unless they are bench, injured reserve, or ' '
            if positionId not in ["20", "21", "24"]:
                starting_roster_slots[position] = roster[positionId]
    # Add roster_slots{} and starting_roster_slots{} as a league attribute
    league.roster_settings = {
        "roster_slots": roster_slots,
        "starting_roster_slots": starting_roster_slots,
    }
    return


def set_owner_names(league: League) -> None:
    """This function sets the owner names for each team in the league.
    The team.owners attribute contains a dictionary of information with owner details, not a simple name.

    Args:
        league (League): ESPN League object
    """
    # Set the owner name for each team
    for team in league.teams:
        if team.owners and all(
            [key in team.owners[0].keys() for key in ["firstName", "lastName"]]
        ):
            team.owner = re.sub(
                " +",
                " ",
                team.owners[0]["firstName"] + " " + team.owners[0]["lastName"],
            ).title()
        else:
            team.owner = "Unknown Owner"

        if str(league.league_id) == "1086064":
            # Map owners of previous/co-owned teams to current owners to preserve "franchise"
            team.owner = OWNER_MAP.get(team.owner, team.owner)


def set_additional_settings(league: League) -> None:
    """This function adds additional league settings to the League object.

    Args:
        league (League): ESPN League object
    """
    # Create a dictionary that maps each week to the matchup period it is in
    # This is necessary because some matchup periods span multiple weeks
    league.settings.week_to_matchup_period = {}
    for matchup_period, weeks in league.settings.matchup_periods.items():
        for week in weeks:
            league.settings.week_to_matchup_period[week] = int(matchup_period)


def set_completed_games(league: League):
    """This function identifies how many weeks in a season are completed.
    We must check each team's number of matchups completed, since some teams
    could have had a bye.

    Args:
        league (League): The league
    """
    n_completed_weeks = 0
    for team in league.teams:
        n_completed_weeks = max(
            n_completed_weeks, sum([1 if o != "U" else 0 for o in team.outcomes])
        )
    league.n_completed_weeks = n_completed_weeks


def standings_weekly(self: League, week: int) -> List[Team]:
    """TEMPORARY FUNCTION!!
    A PR has been submitted to the espn-api package to fix the standings_weekly() function.
    Until that is merged, this function can be used to replace the standings_weekly() function.
    """
    # Return empty standings if no matchup periods have completed yet
    if self.currentMatchupPeriod <= 1:
        return self.standings()

    # Get standings data for each team up to the given week
    list_of_team_data = []
    for team in self.teams:
        team_data = {
            "team": team,
            "team_id": team.team_id,
            "division_id": team.division_id,
            "wins": sum([1 for outcome in team.outcomes[:week] if outcome == "W"]),
            "ties": sum([1 for outcome in team.outcomes[:week] if outcome == "T"]),
            "losses": sum([1 for outcome in team.outcomes[:week] if outcome == "L"]),
            "points_for": sum(team.scores[:week]),
            "points_against": sum([team.schedule[w].scores[w] for w in range(week)]),
            "schedule": team.schedule[:week],
            "outcomes": team.outcomes[:week],
        }
        team_data["win_pct"] = (team_data["wins"] + team_data["ties"] / 2) / sum(
            [1 for outcome in team.outcomes[:week] if outcome in ["W", "T", "L"]]
        )
        list_of_team_data.append(team_data)

    # Identify the proper tiebreaker hierarchy
    if self.settings.playoff_seed_tie_rule == "TOTAL_POINTS_SCORED":
        tiebreaker_hierarchy = [
            (sort_by_win_pct, "win_pct"),
            (sort_by_points_for, "points_for"),
            (sort_by_head_to_head, "h2h_wins"),
            (sort_by_division_record, "division_record"),
            (sort_by_points_against, "points_against"),
            (sort_by_coin_flip, "coin_flip"),
        ]
    elif self.settings.playoff_seed_tie_rule == "H2H_RECORD":
        tiebreaker_hierarchy = [
            (sort_by_win_pct, "win_pct"),
            (sort_by_head_to_head, "h2h_wins"),
            (sort_by_points_for, "points_for"),
            (sort_by_division_record, "division_record"),
            (sort_by_points_against, "points_against"),
            (sort_by_coin_flip, "coin_flip"),
        ]
    elif self.settings.playoff_seed_tie_rule == "INTRA_DIVISION_RECORD":
        tiebreaker_hierarchy = [
            (sort_by_division_record, "division_record"),
            (sort_by_head_to_head, "h2h_wins"),
            (sort_by_win_pct, "win_pct"),
            (sort_by_points_for, "points_for"),
            (sort_by_points_against, "points_against"),
            (sort_by_coin_flip, "coin_flip"),
        ]
    else:
        raise ValueError(
            "Unkown tiebreaker_method: Must be either 'TOTAL_POINTS_SCORED', 'H2H_RECORD', or 'INTRA_DIVISION_RECORD'"
        )

    # First assign the division winners
    division_winners = []
    for division_id in list(self.settings.division_map.keys()):
        division_teams = [
            team_data
            for team_data in list_of_team_data
            if team_data["division_id"] == division_id
        ]
        division_winner = sort_team_data_list(division_teams, tiebreaker_hierarchy)[0]
        division_winners.append(division_winner)
        list_of_team_data.remove(division_winner)

    # Sort the division winners
    sorted_division_winners = sort_team_data_list(
        division_winners, tiebreaker_hierarchy
    )

    # Then sort the rest of the teams
    sorted_rest_of_field = sort_team_data_list(list_of_team_data, tiebreaker_hierarchy)

    # Combine all teams
    sorted_team_data = sorted_division_winners + sorted_rest_of_field

    return [team_data["team"] for team_data in sorted_team_data]


# TEMPORARY: use the fixed standings function
League.standings_weekly = standings_weekly


def fetch_league(
    league_id: int, year: int, swid: Optional[str] = None, espn_s2: Optional[str] = None
) -> League:
    """
    This function is a wrapper around the League object.
    Given the same inputs, it will instantiate a League object and add other details such as:
        - league.cookies
        - league.endpoint
        - league.settings.roster_slots
        - league.settings.starting_roster_slots
        - Set the roster for the current week
    """

    print("[BUILDING LEAGUE] Fetching league data...")
    league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)

    # Set cookies
    league.cookies = {"swid": swid, "espn_s2": espn_s2}

    # Set league endpoint
    set_league_endpoint(league)
    verify_league_is_active(league)

    # Get roster information
    get_roster_settings(league)

    # Set additinoal settings
    set_additional_settings(league)
    set_completed_games(league)

    # Set the owners for each team
    set_owner_names(league)

    # # Cache this function to speed up processing
    # league.box_scores = functools.cache(league.box_scores)

    # Use `matchup period` as `week` throughout the code
    current_matchup_period = league.settings.week_to_matchup_period[
        max(league.current_week, 1)
    ]

    # Load current league data
    print("[BUILDING LEAGUE] Loading current league details...")
    league.current_week = current_matchup_period
    league.load_roster_week(current_matchup_period)

    return league
