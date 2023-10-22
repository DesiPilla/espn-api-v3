import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from typing import Dict, List, Optional, Tuple
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


def simulate_matchups(
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
    league: League,
    standings: Optional[pd.DataFrame] = None,
    first_week_to_simulate: Optional[int] = None,
    matchups_to_exclude: Dict[int, List[PseudoMatchup]] = {},
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
        first_week_to_simulate (Optional[int]): First week to include in the simulation. Defaults to None.
            - If first_week_to_simulate = 10, the function will simulate all matchups from Weeks 10 -> end of season.
            - If None, the function will use `standings` to imply how many weeks have finished already and simulate the rest.

    Returns:
        pd.DataFrame: Simulated standings dataframe
    """

    if standings is None:
        # Get current standings
        standings = build_standings(league)

    if first_week_to_simulate is None:
        first_week_to_simulate = (
            standings[["wins", "ties", "losses"]].sum(axis=1).min() + 1
        )

    matchups = []  # type: List
    for week in range(first_week_to_simulate, league.settings.reg_season_count + 1):  # type: ignore
        # Get matchups for the given week
        week_matchups = []
        for team in league.teams:
            (home_team, away_team) = sorted(
                [team, team.schedule[week - 1]], key=lambda x: x.team_id
            )

            # Only add matchup if it the team doesn't already have an outcome for it
            if (
                week in matchups_to_exclude.keys()
                and PseudoMatchup(home_team, away_team) in matchups_to_exclude[week]
            ):
                continue
            else:
                week_matchups.append(PseudoMatchup(home_team, away_team))

        matchups.extend(set(week_matchups))

    # Predict each matchup and update the standings
    standings = simulate_matchups(matchups, standings)

    standings = sort_standings(standings)
    made_playoffs = [1] * league.settings.playoff_team_count + [0] * (
        len(league.teams) - league.settings.playoff_team_count
    )
    standings["made_playoffs"] = made_playoffs
    standings["final_rank"] = standings.reset_index().index + 1
    return standings


def input_outcomes(
    league: League,
    standings: pd.DataFrame,
    week: int,
    outcomes: Optional[List[int]] = None,
) -> Tuple[pd.DataFrame, Dict[int, List[PseudoMatchup]]]:
    """
    This function will fetch the matchups for a given week and prompt the user to choose a winner.
    (The `outcomes` parameter can hold information instead of requiring user input)

    The 'wins', 'ties', and 'losses' fields of the standings dataframe will then be updated to reflect
    the user's selections.

    The 'points_for' field, however, will NOT be updated.

    Args:
        league (League): League
        standings (pd.DataFrame): Standings dataframe
        week (int): Week to select matchup outcomes for
        outcomes (List[int]): Outcomes passed in as an argument instead of user input. Defaults to None

    Raises:
        Exception: Incorrect user input

    Returns:
        pd.DataFrame: Updated standings dataframe
    """
    standings = standings.copy()
    matchups_to_exclude = {week: []}  # type: dict
    box_scores = league.box_scores(week)
    for i, matchup in enumerate(box_scores):
        if outcomes is None:
            winner = int(
                input(
                    f"Who will win this matchup?\n (1) {matchup.home_team.owner}\n (2) {matchup.away_team.owner}\n (3) Leave blank"
                )
            )
        else:
            winner = outcomes[i]
        if winner == 3:
            # No winner assigned
            continue

        else:
            if winner == 1:
                (home_outcome, away_outcome) = [(1, 0, 0), (0, 0, 1)]
            elif winner == 2:
                (home_outcome, away_outcome) = [(0, 0, 1), (1, 0, 0)]
            else:
                raise Exception("Incorrect input type. Please enter `1` or `2`.")

            # Update standings
            standings.loc[matchup.home_team.team_id, "wins"] += home_outcome[0]  # type: ignore
            standings.loc[matchup.home_team.team_id, "losses"] += home_outcome[2]  # type: ignore
            standings.loc[matchup.away_team.team_id, "wins"] += away_outcome[0]  # type: ignore
            standings.loc[matchup.away_team.team_id, "losses"] += away_outcome[2]  # type: ignore

            # Assign the team with the smaller team_id as the "home team"
            (home_team, away_team) = sorted(
                [matchup.home_team, matchup.away_team], key=lambda x: x.team_id
            )
            # Add matchup to list of excluded matchups
            matchups_to_exclude[week].append(PseudoMatchup(home_team, away_team))

    return standings, matchups_to_exclude


def get_rank_distribution(final_standings: pd.DataFrame) -> pd.DataFrame:
    """This function accepts a dataframe of simulated final standings (pd.concat of simulate_season())
    and uses it to calculate the distribution of final ranks for each team.

    The dataframe will tell you the percentage of times each team finished in each position.

    Args:
        final_standings (pd.DataFrame): Dataframe of simulated final standings

    Returns:
        pd.DataFrame: Dataframe containing the distribution of final ranks for each team
    """
    # Extract the number of simulations in the dataframe
    n = final_standings.groupby(["team_name", "team_id"]).count().max().max()

    # Get the number of times each team finished in each final_rank
    rank_dist_df = (
        final_standings.groupby(["team_name", "team_id", "final_rank"])
        .size()
        .reset_index()
        .pivot(index=["team_name", "team_id"], columns="final_rank", values=0)
        .fillna(0)
        .astype(int)
    )

    # Normalize the values to be percentages
    rank_dist_df /= n / 100

    # Calculate the playoff odds for each team and join it to the dataframe
    rank_dist_df = rank_dist_df.join(
        final_standings.groupby(["team_name", "team_id"])
        .mean()["made_playoffs"]
        .rename("playoff_odds")
        * 100
    ).sort_values("playoff_odds", ascending=False)

    return rank_dist_df


def simulate_season(
    league: League,
    n: int = 1000,
    what_if: Optional[bool] = False,
    outcomes: Optional[List[int]] = None,
    random_state: Optional[int] = 42,
) -> pd.DataFrame:
    """
    This function simulates the rest of a season by running n Monte-Carlo simulations.
    The `what_if` parameter allows the user to specify the outcomes of the current week (but not the scores) if desired
    (this can be done to see the effect of an outcome on a team's playoff odds.)

    Args:
        league (League): League
        n (int): Number of Monte Carlo simulations to run
        what_if (Optional[bool]): Manually specify the outcomes of the current week? Defaults to False
        outcomes (List[int]): Outcomes passed in as an argument instead of user input. Defaults to None
        random_state (Optional[int]): Random seed. Defaults to 42.

    Returns:
        pd.DataFrame: Dataframe containing results of the simulation
    """
    np.random.seed(random_state)

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
        first_week_to_simulate = (
            standings[["wins", "ties", "losses"]].sum(axis=1).iloc[0] + 1
        )
        standings, matchups_to_exclude = input_outcomes(
            league=league,
            standings=standings,
            week=league.current_week,
            outcomes=outcomes,
        )
    else:
        first_week_to_simulate = None
        matchups_to_exclude = {}

    if first_week_to_simulate is not None:
        print(
            f"""Simulating from week {first_week_to_simulate} to {league.settings.reg_season_count}"""
        )
    else:
        print(
            f"""Simulating from week {standings[["wins", "ties", "losses"]].sum(axis=1).iloc[0] + 1} to {league.settings.reg_season_count}"""
        )

    def simulate_single_season_parallel():
        return simulate_single_season(
            league=league,
            standings=standings.copy(),
            first_week_to_simulate=first_week_to_simulate,
            matchups_to_exclude=matchups_to_exclude,
        )

    final_standings = pd.concat(
        Parallel(n_jobs=-1, verbose=1)(
            delayed(simulate_single_season_parallel)() for i in range(n)
        )
    )

    # Record those who made the playoffs in the simulated season
    for team_id, stats in final_standings.iterrows():
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
        lower=0.1, upper=99.9
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

    # Get the distribution of final positions for each team
    rank_dist = get_rank_distribution(final_standings)

    # Add team details to the dataframe
    def get_team_info(s):
        team = league.teams[int(s.team_id - 1)]
        s["team_owner"] = team.owner
        s["team_name"] = team.team_name
        return s

    playoff_odds = playoff_odds.apply(get_team_info, axis=1)
    rank_dist = rank_dist.reset_index().apply(get_team_info, axis=1)

    return (
        playoff_odds[
            [
                "team_owner",
                "team_name",
                "wins",
                "ties",
                "losses",
                "points_for",
                "playoff_odds",
            ]
        ].sort_values(by="playoff_odds", ascending=False),
        rank_dist,
    )


def get_outcomes_if_team_wins(
    team: Team, week: int, matchups: List[Matchup]
) -> List[int]:
    """
    This function returns an `outcomes` list that indicates the input team won its matchup, and all other matchups are left blank.

    Args:
        team (Team): Team that won
        week (int): Week
        matchups (List[Matchup]): List of matchups for the week (from league.box_scores(week))

    Returns:
        List[int]: list of outcomes to be passed into input_outcomes().
    """
    outcomes = []
    for matchup in matchups:
        if team.team_id == matchup.home_team.team_id:
            outcomes.append(1)
        elif team.team_id == matchup.away_team.team_id:
            outcomes.append(2)
        else:
            outcomes.append(3)
    return outcomes


def playoff_odds_swing(league: League, week: int, n: int = 100) -> pd.DataFrame:
    """
    This function determines how much a team's playoff odds will change based on if they win or lose their next matchup.

    For each matchup, two simulations are run:
        - one where the home team wins, and
        - one where the away team wins

        In each simulation, only the one matchup is pre-determined. All other matchups in that week are simulated.

        The difference between the home and away teams' playoff odds in the two simulations is called the "swing".
            - If the simulated playoff odds for a team is 75% if they win and 50% if they lose, then the "swing" is 25%

    The playoff "swings" for each team is returned as a pandas Series where "team_owner" is the index.

    Args:
        league (League): League
        week (int): First week to include in the simulation.
            - If first_week_to_simulate = 10, the function will simulate all matchups from Weeks 10 -> end of season.
        n (int): Number of Monte Carlo simulations to run

    Returns:
        pd.DataFrame: Difference in playoff odds for each team if they win vs if they lose
    """
    # Get all matchups for the week.
    matchups = league.box_scores(week)

    # Instantiate the series
    odds_diff = pd.DataFrame(dtype=float)

    # Simulate playoff odds based on outcome of each matchup
    for matchup in matchups:
        # Simulate season if home team wins
        home_team = matchup.home_team
        outcomes_home_win = get_outcomes_if_team_wins(home_team, week, matchups)
        odds_home_win, _ = simulate_season(
            league, n, what_if=True, outcomes=outcomes_home_win
        ).set_index("team_owner")

        # Simulate season if away team wins
        away_team = matchup.away_team
        outcomes_away_win = get_outcomes_if_team_wins(away_team, week, matchups)
        odds_away_win, _ = simulate_season(
            league, n, what_if=True, outcomes=outcomes_away_win
        ).set_index("team_owner")

        # Merge results
        odds = pd.merge(
            odds_home_win[["playoff_odds"]],
            odds_away_win[["playoff_odds"]],
            suffixes=("_if_home_win", "_if_away_lose"),
            left_index=True,
            right_index=True,
        )
        odds["playoff_odds_if_win"], odds["playoff_odds_if_lose"] = odds.max(
            axis=1
        ), odds.min(axis=1)

        # Calculate difference in playoff odds
        odds["swing"] = odds["playoff_odds_if_win"] - odds["playoff_odds_if_lose"]

        odds_diff = pd.concat(
            [
                odds_diff,
                odds[["playoff_odds_if_win", "playoff_odds_if_lose", "swing"]]
                .abs()
                .loc[[home_team.owner, away_team.owner]],
            ]
        )

    return odds_diff
