import pandas as pd
from typing import Optional


def filter_df(
    df: pd.DataFrame,
    team_owner: Optional[str] = None,
    opp_owner: Optional[str] = None,
    year: Optional[int] = None,
    week: Optional[int] = None,
    division: Optional[str] = None,
    meaningful: Optional[bool] = None,
    is_playoff: Optional[bool] = None,
    is_regular_season: Optional[bool] = None,
    outcome: Optional[str] = None,
) -> pd.DataFrame:
    """Filter a historical stats dataframe by some fields.
    Only records that match all conditions will be returned.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        team_owner (str): Team owner to filter to
        opp_owner (str): Opponent owner to filter to
        year (int): Year to filter to
        week (int): Week to filter to
        division (str): Division to filter to
        meaningful (bool): Include only 'meaningful' games
        is_playoff_game (bool): Include only playoff games games
        is_regular_season (bool): Include only regular season games
        outcome (str): Outcome to filter to ('win', 'lose', 'tie')

    Returns:
        df (pd.DataFrame): Filtered dataframe
    """
    if team_owner is not None:
        df = df[df.team_owner == team_owner]
    if opp_owner is not None:
        df = df[df.opp_owner == opp_owner]
    if year is not None:
        df = df[df.year == year]
    if week is not None:
        df = df[df.week == week]
    if division is not None:
        df = df[df.division == division]
    if meaningful is not None:
        df = df[df.is_meaningful_game == meaningful]
    if is_playoff is not None:
        df = df[df.is_playoff == is_playoff]
    if is_regular_season is not None:
        df = df[df.is_regular_season == is_regular_season]
    if outcome is not None:
        df = df[df.outcome == outcome]
    return df


def exclude_df(
    df: pd.DataFrame,
    team_owner: Optional[str] = None,
    year: Optional[int] = None,
    week: Optional[int] = None,
    division: Optional[str] = None,
    meaningful: Optional[bool] = None,
    outcome: Optional[str] = None,
) -> pd.DataFrame:
    """Filter a historical stats dataframe by some fields.
    Only records that match all conditions will be excluded.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        team_owner (str): Team owner to exclude
        year (int): Year to exclude
        week (int): Week to exclude
        division (str): Division to exclude
        meaningful (bool): Exclude only 'meaningful' games
        outcome (str): Outcome to exclude to ('win', 'lose', 'tie')

    Returns:
        df (pd.DataFrame): Filtered dataframe
    """
    conditions = [True] * len(df)
    if team_owner is not None:
        conditions &= df.team_owner == team_owner
    if year is not None:
        conditions &= df.year == year
    if week is not None:
        conditions &= df.week == week
    if division is not None:
        conditions &= df.division == division
    if meaningful is not None:
        conditions &= df.meaningful == meaningful
    if outcome is not None:
        conditions &= df.outcome == outcome
    return df[~conditions]  # type: ignore


def exclude_most_recent_week(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out the most recent week of matchups from the historical stats dataframe.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    year_to_exclude = df.year.max()
    week_to_exclude = filter_df(df, year=year_to_exclude).week.max()
    return exclude_df(df, year=year_to_exclude, week=week_to_exclude)


def get_any_records(
    df: pd.DataFrame,
    year: int,
    week: int,
    stat: str,
    high_first: bool = True,
    n: int = 5,
) -> pd.DataFrame:
    """Check if a team recorded a top-5 (or n) statistic was posted during the most recent week.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        year (int): Year to check for a record
        week (int): Week to check for a record
        stat (str): The stat of note ('team_score', 'QB_pts', etc.)
        stat_units (str): ('pts', 'pts/gm', etc.)
        high_first (bool): Are higher values better than lower values?. Defaults to True.
        n (int): How far down the record list to check (defaults to 5)
    """
    # Rank each row by the stat of note
    sub_df = df.dropna(subset=stat)
    sub_df["rank"] = sub_df[stat].rank(ascending=(not high_first), method="min")

    # Keep only the top n records, in the year-week of note
    sub_df = sub_df[sub_df["rank"] <= n]
    sub_df = filter_df(sub_df, year=year, week=week)

    return sub_df[["year", "week", "team_owner", stat, "rank"]]
