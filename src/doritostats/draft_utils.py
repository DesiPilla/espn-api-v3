import numpy as np
import pandas as pd
from typing import Optional
from .fetch_utils import fetch_league, OWNER_MAP
from espn_api.football import League


def get_draft_details(league: League) -> pd.DataFrame:
    """For a given league, get details about the draft that year.
    Each row includes information about a pick, such as:
        - round_num, round_pick, player_name, player_id, position, proj_points, etc.

    Args:
        league (League): League

    Returns:
        pd.DataFrame: Draft dataframe
    """
    draft = pd.DataFrame()

    # Get a dictionary of the starting roster slots and number of each for the League (Week 1 must have passed already)
    primary_slots = [
        slot
        for slot in league.roster_settings["starting_roster_slots"].keys()
        if ("/" not in slot) or (slot == "D/ST")
    ]

    for i, player in enumerate(league.draft):
        draft.loc[i, "year"] = league.year
        draft.loc[i, "team_owner"] = player.team.owner.title()
        draft.loc[i, "team_id"] = player.team.team_id
        draft.loc[i, "player_name"] = player.playerName
        draft.loc[i, "player_id"] = player.playerId
        draft.loc[i, "round_num"] = player.round_num
        draft.loc[i, "round_pick"] = player.round_pick
        try:
            # Get more player details (can take 1.5 min)
            player = league.player_info(playerId=draft.loc[i, "player_id"])
            draft.loc[i, "pro_team"] = player.proTeam
            draft.loc[i, "proj_points"] = player.projected_total_points
            draft.loc[i, "total_points"] = player.total_points
            draft.loc[i, "position"] = [
                slot for slot in player.eligibleSlots if slot in primary_slots
            ][0]
        except AttributeError:
            print("Pick {} missing.".format(i + 1))
            draft.loc[i, "player_name"] = ""
            draft.loc[i, "player_id"] = ""
            draft.loc[i, "round_num"] = 99
            draft.loc[i, "round_pick"] = 99
        except Exception:
            print(i, player, league.draft[i - 2 : i + 2])
            draft.loc[i, "position"] = player.eligibleSlots[0]

    # Map owners of previous/co-owned teams to current owners to preserve "franchise"
    draft.replace({"team_owner": OWNER_MAP, "opp_owner": OWNER_MAP}, inplace=True)

    # Add some additional columns
    draft["first_letter"] = draft.player_name.str[0]
    draft["points_surprise"] = draft.total_points - draft.proj_points
    draft["positive_surprise"] = draft.points_surprise > 0
    draft["pick_num"] = (draft.round_num - 1) * len(
        draft.team_id.unique()
    ) + draft.round_pick

    # Add the value associated with each pick
    draft_pick_values = pd.read_csv("./src/doritostats/pick_value.csv")
    draft = pd.merge(
        draft, draft_pick_values, left_on="pick_num", right_on="pick", how="left"
    ).drop(columns=["pick"])
    return draft


def get_multiple_drafts(
    league_id: int,
    start_year: int = 2020,
    end_year: int = 2021,
    swid: Optional[str] = None,
    espn_s2: Optional[str] = None,
) -> pd.DataFrame:
    """This function generates a dataframe containing draft data for a league across multiple years.

    Args:
        league_id (int): League
        start_year (int, optional): First year to get draft stats for. Defaults to 2020.
        end_year (int, optional): Final year to get draft stats for (inclusive). Defaults to 2021.
        swid (Optional[str], optional): User credential. Defaults to None.
        espn_s2 (Optional[str], optional): User credential. Defaults to None.

    Returns:
        pd.DataFrame: Draft dataframe
    """
    draft = pd.DataFrame()
    for year in range(start_year, end_year + 1):
        print("Fetching {} draft...".format(year), end="")
        try:
            draft_league = fetch_league(
                league_id=league_id, year=year, swid=swid, espn_s2=espn_s2
            )
        except Exception:
            continue

        draft = pd.concat([draft, get_draft_details(draft_league)])

    return draft


def get_team_max(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """For each team in the draft history dataframe, return the value that occurs most for a given column.

    Args:
        df (pd.DataFrame): Draft history dataframe
        col (str): Column name

    Returns:
        pd.DataFrame: values
    """
    df_mode = df.groupby(["team_owner"])[col].agg(pd.Series.mode)

    # Ugly code that essentially joins back to the original df to get the count of the mode
    max_vals = df_mode.values
    df_mode = df_mode.to_frame()
    df_mode[col] = [v[0] if type(v) == np.ndarray else v for v in max_vals]
    value_counts = (
        df.groupby(["team_owner"])[col]
        .value_counts()
        .reset_index(name="count")
        .set_index(["team_owner", col])
    )
    df_mode = df_mode.reset_index().join(value_counts, on=["team_owner", col])
    df_mode[col] = max_vals
    return df_mode.sort_values(by="count", ascending=False)
