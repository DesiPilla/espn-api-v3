import datetime
import functools
import logging
import os
import re
import requests
import warnings
from typing import Optional

import numpy as np
import pandas as pd
import datetime
from typing import Optional
from espn_api.football import League
from espn_api.requests.constant import FANTASY_BASE_ENDPOINT
import sqlalchemy
from dotenv import load_dotenv

from backend.src.doritostats.exceptions import InactiveLeagueError

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

OWNER_MAP = {
    "Katie Brooks": "Nikki Pilla",
    "Joseph Ricupero": "Jojo & Matt",
}


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

    return sqlalchemy.create_engine(conn_str, pool_pre_ping=True)


def get_league_creds(league_id: int, year: Optional[int] = None):
    """Get the league credentials for a given league_id and year."""
    conn = get_postgres_conn()

    # Query all the league info data
    sql = "SELECT * FROM public.fantasy_stats_leagueinfo WHERE league_id = {}".format(
        league_id
    )
    league_info_df = pd.read_sql(sql, conn)

    if year is None:
        return (
            league_info_df.sort_values(by="league_year", ascending=False).iloc[0].values
        )
    else:
        league_creds = league_info_df[league_info_df.league_year == year].iloc[0]
        if league_creds.empty:
            raise Exception(
                "No league credentials found for league_id {} and year {}".format(
                    league_id, year
                )
            )
        return league_creds.values


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

    logger.info("[BUILDING LEAGUE] League endpoint set to: {}".format(league.endpoint))


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
    if not r["status"]["isActive"]:
        raise Exception(
            "League {} is not active. The league must be activated on ESPN to use.".format(
                league.league_id
            )
        )
    logger.info("[BUILDING LEAGUE] League is active.")


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
    if not r["status"]["isActive"]:
        raise InactiveLeagueError(
            "League {} is not active. The league must be activated on ESPN to use.".format(
                league.league_id
            )
        )
    print("[BUILDING LEAGUE] League is active.")


def get_roster_settings(league: League) -> None:
    """This grabs the roster and starting lineup settings for the league
    - Grabs the dictionary containing the number of players of each position a roster contains
    - Creates a dictionary roster_slots{} that only inlcludes slotIds that have a non-zero number of players on the roster
    - Creates a dictionary starting_roster_slots{} that is a subset of roster_slots{} and only includes slotIds that are on the starting roster
    - Add roster_slots{} and starting_roster_slots{} to the League attribute League.rosterSettings
    """
    logger.info("[BUILDING LEAGUE] Gathering roster settings information...")

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

    logger.info("[BUILDING LEAGUE] Fetching league data...")
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

    # Set the owners for each team
    set_owner_names(league)

    # # Cache this function to speed up processing
    # league.box_scores = functools.cache(league.box_scores)

    # Load current league data
    logger.info("[BUILDING LEAGUE] Loading current league details...")
    league.current_week = max(league.current_week, 1)
    current_matchup_period = league.settings.week_to_matchup_period[league.current_week]
    league.load_roster_week(current_matchup_period)

    return league
