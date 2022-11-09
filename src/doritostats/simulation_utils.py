from typing import List, Optional
import numpy as np
import pandas as pd
from espn_api.football import League, Team, Matchup
from src.doritostats.fetch_utils import PseudoMatchup


def sort_standings(
    standings: pd.DataFrame, tie_breaker_rule: Optional[str] = None
) -> pd.DataFrame:
    """This function sorts a standings dataframe according to a leagues tiebreaker rules.
    The standings dataframe will be sorted such that the first n teams are those the qualify for the playoffs
    and the bottom teams are those that do not qualify.

    Args:
        standings (pd.DataFrame): Standings dataframe from build_standings()
        tie_breaker_rule (Optional[str], optional): league.settings.playoff_seed_tie_rule. Defaults to None.

    Returns:
        pd.DataFrame: Standings dataframe sorted
    """
    # ASSUME Playoff Seeding Tie Breaker is "Total Points For"
    # since API doesn't seem to get this data correctly
    standings = standings.sort_values(by=["wins", "points_for"], ascending=False)

    return standings


def build_standings(league: League) -> pd.DataFrame:
    """This function builds the current leaderboard for a league

    Args:
        league (League): League object

    Returns:
        pd.DataFrame: standings dataframe
    """
    standings = pd.DataFrame()
    standings["team_id"] = [team.team_id for team in league.teams]
    standings["team_name"] = [team.team_name for team in league.teams]
    standings["wins"] = [team.wins for team in league.teams]
    standings["ties"] = [team.ties for team in league.teams]
    standings["losses"] = [team.losses for team in league.teams]
    standings["points_for"] = [team.points_for for team in league.teams]
    standings.set_index("team_id", inplace=True)

    return sort_standings(standings)


def simulate_score(team: Team) -> float:
    """Generate a team score.
    The score is randomly selected from a normal distribution defined by:
        mean = average score over the last 6 weeks
        std = standard deviation over the entire season * 2

    Args:
        team (Team): Team to gennerate score for

    Returns:
        float: predicted score
    """
    scores = np.array(team.scores)
    scores = scores[scores > 0]
    return np.random.normal(
        scores[-6:].mean(), scores.std() * 2
    )  # Artificially inflate the stdev since scores are highly unpredictable


def simulate_matchup(
    matchup: Matchup,
) -> tuple[tuple[int, int, int, float], tuple[int, int, int, float]]:
    """Simulate a matchup between two teams by randomly generating scores based on preivous team performance.

    Args:
        matchup (Matchup): the mathcup to simulate the outcome of

    Returns:
        tuple[tuple[int, int, int, float], tuple[int, int, int, float]]:
            * (home_outcome, away_outcome) where:
                outcome = (win?, tie?, loss?, score)
            * if the home team won 100 - 90, the result would be:
                ((1, 0, 0, 100), (0, 0, 1, 90))

    """
    home_score = simulate_score(matchup.home_team)
    away_score = simulate_score(matchup.away_team)
    if home_score > away_score:
        return ((1, 0, 0, home_score), (0, 0, 1, away_score))
    elif away_score > home_score:
        return ((0, 0, 1, home_score), (1, 0, 0, away_score))
    else:
        return ((0, 1, 0, home_score), (0, 1, 0, away_score))


def simulate_week(
    matchups: List[PseudoMatchup], standings: pd.DataFrame
) -> pd.DataFrame:
    """Simulate all matchups in a week.
    The standings dataframe is then updated to reflect the outcome of the simulated matchups.

    Args:
        matchups (List[PseudoMatchup]): List of matchups to simulate
        standings (pd.DataFrame): Standings dataframe

    Returns:
        pd.DataFrame: Updated standings dataframe
    """

    # Predict each matchup and update the standings
    for matchup in matchups:
        (home_outcome, away_outcome) = simulate_matchup(matchup)
        standings.loc[matchup.home_team.team_id, "wins"] += home_outcome[0]  # type: ignore
        standings.loc[matchup.home_team.team_id, "ties"] += home_outcome[1]  # type: ignore
        standings.loc[matchup.home_team.team_id, "losses"] += home_outcome[2]  # type: ignore
        standings.loc[matchup.home_team.team_id, "points_for"] += home_outcome[3]  # type: ignore

        standings.loc[matchup.away_team.team_id, "wins"] += away_outcome[0]  # type: ignore
        standings.loc[matchup.away_team.team_id, "ties"] += away_outcome[1]  # type: ignore
        standings.loc[matchup.away_team.team_id, "losses"] += away_outcome[2]  # type: ignore
        standings.loc[matchup.away_team.team_id, "points_for"] += away_outcome[3]  # type: ignore

    return standings


def simulate_single_season(
    league: League, standings: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """This function simulates a season.
    If no standings dataframe is passed in, one will be generated based on the current state of the league.
    If an initialized standings dataframe is passed in, it will be used.

    The simulation will begin for all matchups AFTER the state of the standings.
    I.e., if the standings dataframe reflects the league standings through Week 9, then this function
    will simulate the remaining weeks (Week 10 through the end of the regular season).

    A column `made_playoffs` will be appended to the standings dataframe at the end
    of the simulation that indicates whether or not the team qualified for the playoffs.

    Args:
        league (League): League
        standings (Optional[pd.DataFrame]): Initialized standings dataframe. Defaults to None.

    Returns:
        pd.DataFrame: Simulated standings dataframe
    """

    if standings is None:
        # Get current standings
        standings = build_standings(league)

    first_week_to_simulate = (
        standings[["wins", "ties", "losses"]].sum(axis=1).iloc[0] + 1
    )
    for week in range(first_week_to_simulate, league.settings.reg_season_count + 1):
        # Get matchups for the given week
        matchups_dict = {}
        for team in league.teams:
            (home_team, away_team) = sorted(
                [team, team.schedule[week - 1]], key=lambda x: x.team_id
            )
            matchups_dict[home_team.team_id] = PseudoMatchup(home_team, away_team)
        matchups = list(matchups_dict.values())

        # Predict each matchup and update the standings
        standings = simulate_week(matchups, standings)

    standings = sort_standings(standings)
    made_playoffs = [1] * league.settings.playoff_team_count + [0] * (
        len(league.teams) - league.settings.playoff_team_count
    )
    standings["made_playoffs"] = made_playoffs
    return standings


def input_outcomes(league: League, standings: pd.DataFrame, week: int) -> pd.DataFrame:
    """
    This function will fetch the matchups for a given week and prompt the user to choose a winner.

    The 'wins', 'ties', and 'losses' fields of the standings dataframe will then be updated to reflect
    the user's selections.

    The 'points_for' field, however, will NOT be updated.

    Args:
        league (League): League
        standings (pd.DataFrame): Standings dataframe
        week (int): Week to select matchup outcomes for

    Raises:
        Exception: Incorrect user input

    Returns:
        pd.DataFrame: Updated standings dataframe
    """
    box_scores = league.box_scores(week)
    for matchup in box_scores:
        winner = int(
            input(
                f"Who will win this matchup?\n (1) {matchup.home_team.owner}\n (2) {matchup.away_team.owner}\n"
            )
        )
        if winner == 1:
            (home_outcome, away_outcome) = [(1, 0, 0), (0, 0, 1)]
        elif winner == 2:
            (home_outcome, away_outcome) = [(0, 0, 1), (1, 0, 0)]
        else:
            raise Exception("Incorrect input type. Please enter `1` or `2`.")

        standings.loc[matchup.home_team.team_id, "wins"] += home_outcome[0]  # type: ignore
        standings.loc[matchup.home_team.team_id, "losses"] += home_outcome[2]  # type: ignore
        standings.loc[matchup.away_team.team_id, "wins"] += away_outcome[0]  # type: ignore
        standings.loc[matchup.away_team.team_id, "losses"] += away_outcome[2]  # type: ignore

    return standings


def simulate_season(
    league: League, n: int = 1000, what_if: Optional[bool] = False
) -> pd.DataFrame:
    """
    This function simulates the rest of a season by running n Monte-Carlo simulations.
    The `what_if` parameter allows the user to specify the outcomes of the current week (but not the scores) if desired
    (this can be done to see the effect of an outcome on a team's playoff odds.)

    Args:
        league (League): League
        n (int): Number of simulations to run
        what_if (Optional[bool]): Manually specify the outcomes of the current week? Defaults to False
        random_state (Optional[int]): Random seed. Defaults to 42.

    Returns:
        pd.DataFrame: Dataframe containing results of the simulation
    """
    playoff_count = {
        team.team_id: {
            "wins": 0,
            "ties": 0,
            "losses": 0,
            "points_for": 0,
            "playoff_odds": 0,
        }
        for team in league.teams
    }

    # Get current standings
    standings = build_standings(league)

    # Manually enter the outcome of the next week
    if what_if:
        standings = input_outcomes(league, standings, league.current_week)

    print(
        f"""Simulating from week {standings[["wins", "ties", "losses"]].sum(axis=1).iloc[0] + 1} to {league.settings.reg_season_count}"""
    )

    for i in range(n):

        # Simulate a single season
        final_standings = simulate_single_season(league, standings.copy())

        # Record those who made the playoffs in the simulated season
        for (team_id, stats) in final_standings.iterrows():
            playoff_count[team_id]["wins"] += stats["wins"]
            playoff_count[team_id]["ties"] += stats["ties"]
            playoff_count[team_id]["losses"] += stats["losses"]
            playoff_count[team_id]["points_for"] += stats["points_for"]
            playoff_count[team_id]["playoff_odds"] += stats["made_playoffs"]

    # Aggregate playoff odds
    playoff_odds = (
        pd.DataFrame.from_dict(
            data=playoff_count,
        )
        .T.reset_index()
        .rename(columns={"index": "team_id"})
    )
    playoff_odds["playoff_odds"] *= 100 / n
    playoff_odds["playoff_odds"] = playoff_odds["playoff_odds"].clip(
        lower=0.01, upper=99.99
    )

    # Get average wins and losses
    playoff_odds["wins"] /= n
    playoff_odds["ties"] /= n
    playoff_odds["losses"] /= n
    playoff_odds["points_for"] /= n

    # Round estimates
    playoff_odds["wins"] = playoff_odds["wins"].round(decimals=1)
    playoff_odds["ties"] = playoff_odds["ties"].round(decimals=1)
    playoff_odds["losses"] = playoff_odds["losses"].round(decimals=1)
    playoff_odds["points_for"] = playoff_odds["points_for"].round(decimals=2)

    # Add team details to the dataframe
    def get_team_info(s):
        team = league.teams[int(s.team_id - 1)]
        s["team_owner"] = team.owner
        s["team_name"] = team.team_name
        return s

    playoff_odds = playoff_odds.apply(get_team_info, axis=1)

    return playoff_odds[
        [
            "team_owner",
            "team_name",
            "wins",
            "ties",
            "losses",
            "points_for",
            "playoff_odds",
        ]
    ].sort_values(by="playoff_odds", ascending=False)
