import pandas as pd


def exclude_most_recent_week(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out the most recent week of matchups from the historical stats dataframe.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    year_to_exclude = df.year.max()
    week_to_exclude = df.query(f"year == {year_to_exclude}").week.max()
    return df.query(f"~(year == {year_to_exclude} & week == {week_to_exclude})")


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
    sub_df = sub_df.query(f"year == {year} & week == {week}")

    return sub_df[["year", "week", "team_owner", stat, "rank"]]