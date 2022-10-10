from typing import Callable
import pandas as pd
from espn_api.football import League, Team


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

def get_wins_leaderboard(df: pd.DataFrame):
    """Get the all time wins leaderboard for the league.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.Series: Ordered leaderboard by career wins
    """
    df = filter_df(df, outcome='win', meaningful=True)
    leaderboard_df = df.groupby('team_owner').count()['outcome'].sort_values(ascending=False).reset_index()
    leaderboard_df.index += 1
    return leaderboard_df


def leaderboard_change(df: pd.DataFrame, leaderboard_func: Callable = get_wins_leaderboard):

    # Get current leaderboard
    current_leaderboard = leaderboard_func(df).reset_index()
    
    # Get leaderboard from last week
    last_week_df = exclude_most_recent_week(df)
    last_week_leaderboard = leaderboard_func(
        last_week_df).reset_index()

    # Merge the leaderboards on 'team_owner'
    leaderboard_change = current_leaderboard.drop(columns=['outcome']).merge(
        last_week_leaderboard.drop(columns=['outcome']), on='team_owner', suffixes=('_current', '_last')).set_index('team_owner')
    
    # Subtract the two weeks to find the change in leaderboard postioning
    leaderboard_change['change'] = leaderboard_change.index_last - \
        leaderboard_change.index_current
    
    return leaderboard_change


def get_team(league: League, team_owner: str):
    for team in league.teams:
        if team.owner == team_owner:
            return team

    raise Exception(f'Owner {team_owner} not in league.')


def get_division_standings(league: League):
    standings = {}
    for division in league.settings.division_map.values():
        teams = [team for team in league.teams if team.division_name == division]
        standings[division] = sorted(teams, key=lambda x: x.standing)
    return standings


def game_of_the_week_stats(league: League, df: pd.DataFrame, owner1: str, owner2: str):
    gow_df = filter_df(df, team_owner=owner1,
                       opp_owner=owner2, meaningful=True)
    gow_df.sort_values(["year", "week"], ascending=True, inplace=True)

    print("{} has won {} / {} matchups.".format(owner1,
          len(filter_df(gow_df, outcome='win')), len(gow_df)))
    print("{} has won {} / {} matchups.".format(owner2,
          len(filter_df(gow_df, outcome='lose')), len(gow_df)))
    print("There have been {} ties".format(
        len(filter_df(gow_df, outcome='tie'))))

    last_matchup = gow_df.iloc[-1]
    print("\nMost recent game: {:.0f} Week {:.0f}".format(
        last_matchup.year, last_matchup.week))
    print("{} {:.2f} - {:.2f} {}".format(last_matchup.team_owner,
                                         last_matchup.team_score,
                                         last_matchup.opp_score,
                                         last_matchup.opp_owner))

    team1 = get_team(league, owner1)
    team2 = get_team(league, owner2)
    division_standings = get_division_standings(league)
    print("\nThis season:\n-----------------------")
    print(f"{owner1} has a record of {team1.wins}-{team1.losses}-{team1.ties}")
    print("They have averaged {:.2f} points per game.".format(
        filter_df(df, team_owner=owner1, year=league.year, meaningful=True).team_score.mean()))
    print("{} is currently {}/{} in the {} division.".format(team1.team_name,
                                                             division_standings[team1.division_name].index(
                                                                 team1) + 1,
                                                             len(
                                                                 division_standings[team1.division_name]),
                                                             team1.division_name))
    print()
    print(f"{owner2} has a record of {team2.wins}-{team2.losses}-{team2.ties}")
    print("They have averaged {:.2f} points per game.".format(
        filter_df(df, team_owner=owner2, year=league.year, meaningful=True).team_score.mean()))
    print("{} is currently {}/{} in the {} division.".format(team2.team_name,
                                                             division_standings[team2.division_name].index(
                                                                 team2) + 1,
                                                             len(
                                                                 division_standings[team2.division_name]),
                                                             team2.division_name))
