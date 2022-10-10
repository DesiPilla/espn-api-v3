from calendar import week
import pandas as pd


def filter_df(df: pd.DataFrame,
              team_owner: str = None,
              opp_owner: str = None,
              year: int = None,
              week: int = None,
              division: str = None,
              meaningful: bool = None,
              outcome: str = None
):
    """ Filter a historical stats dataframe by some fields.
    Only records that match all conditions will be returned.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        team_owner (str): Team owner to filter to
        opp_owner (str): Opponent owner to filter to
        year (int): Year to filter to
        week (int): Week to filter to
        division (str): Division to filter to
        meaningful (bool): Include only 'meaningful' games
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
    if outcome is not None:
        df = df[df.outcome == outcome]
    return df


def exclude_df(df: pd.DataFrame,
              team_owner: str = None,
              year: int = None,
              week: int = None,
              division: str = None,
              meaningful: bool = None,
              outcome: str = None
              ):
    """ Filter a historical stats dataframe by some fields.
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
        conditions *= (df.team_owner == team_owner)
    if year is not None:
        conditions *= (df.year == year)
    if week is not None:
        conditions *= (df.week == week)
    if division is not None:
        conditions *= (df.division == division)
    if meaningful is not None:
        conditions *= (df.meaningful == meaningful)
    if outcome is not None:
        conditions *= (df.outcome == outcome)
    return df[~conditions]

def exclude_most_recent_week(df: pd.DataFrame):
    """Filter out the most recent week of matchups from the historical stats dataframe.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    year_to_exclude = df.year.max()
    week_to_exclude = filter_df(df, year=year_to_exclude).week.max()
    return exclude_df(df, year=year_to_exclude, week=week_to_exclude)
