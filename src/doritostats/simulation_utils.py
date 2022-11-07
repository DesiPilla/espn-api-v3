from typing import List, Optional
import numpy as np
import pandas as pd
from espn_api.football import League, Team, Matchup
from src.doritostats.fetch_utils import PseudoMatchup


def sort_standings(
    standings: pd.DataFrame, tie_breaker_rule: Optional[str] = None
) -> pd.DataFrame:

    # ASSUME Playoff Seeding Tie Breaker is "Total Points For"
    # since API doesn't seem to get this data correctly
    standings = standings.sort_values(by=["wins", "points_for"], ascending=False)

    return standings


def build_standings(league: League) -> pd.DataFrame:
    standings = pd.DataFrame()
    standings["team_id"] = [team.team_id for team in league.teams]
    standings["team_name"] = [team.team_name for team in league.teams]
    standings["wins"] = [team.wins for team in league.teams]
    standings["ties"] = [team.ties for team in league.teams]
    standings["losses"] = [team.losses for team in league.teams]
    standings["points_for"] = [team.points_for for team in league.teams]
    standings["points_against"] = [team.points_against for team in league.teams]
    standings.set_index("team_id", inplace=True)

    return sort_standings(standings)


def get_score_prediction(team: Team) -> float:
    scores = np.array(team.scores)
    scores = scores[scores > 0]
    return np.random.normal(
        scores[-6:].mean(), scores.std() * 2
    )  # Artificially inflate the stdev since scores are highly unpredictable


def simulate_matchup(
    matchup: Matchup,
) -> tuple[tuple[int, int, int, float], tuple[int, int, int, float]]:

    home_score = get_score_prediction(matchup.home_team)
    away_score = get_score_prediction(matchup.away_team)
    if home_score > away_score:
        return ((1, 0, 0, home_score), (0, 0, 1, away_score))
    elif away_score > home_score:
        return ((0, 0, 1, home_score), (1, 0, 0, away_score))
    else:
        return ((0, 1, 0, home_score), (0, 1, 0, away_score))


def simulate_week(
    matchups: List[PseudoMatchup], standings: pd.DataFrame
) -> pd.DataFrame:

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


def simulate_single_season(league: League) -> pd.DataFrame:
    # Get current standings
    standings = build_standings(league)

    for week in range(league.scoringPeriodId, league.settings.reg_season_count + 1):
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


def simulate_season(league: League, n: int = 1000):
    playoff_count = {team.team_id: 0 for team in league.teams}

    for i in range(n):
        # Simulate a single season
        standings = simulate_single_season(league)

        # Record those who made the playoffs in the simulated season
        for (team_id, made_playoffs) in standings.made_playoffs.items():
            playoff_count[team_id] += made_playoffs

    # Aggregate playoff odds
    playoff_odds = pd.DataFrame(
        playoff_count.items(), columns=["team_id", "playoff_odds"]
    )
    playoff_odds["playoff_odds"] *= 100 / n
    playoff_odds["playoff_odds"] = playoff_odds["playoff_odds"].playoff_odds.clip(
        lower=0.01, upper=99.99
    )

    # Add team details to the dataframe
    def get_team_info(s):
        team = league.teams[int(s.team_id - 1)]
        s["team_owner"] = team.owner
        s["team_name"] = team.team_name
        return s

    playoff_odds = playoff_odds.apply(get_team_info, axis=1)

    return playoff_odds[["team_owner", "team_name", "playoff_odds"]].sort_values(
        by="playoff_odds", ascending=False
    )
#         (home_outcome, away_outcome) = [(1, 0, 0), (0, 0, 1)]
#     elif winner == 2:
#         (home_outcome, away_outcome) = [(1, 0, 0), (0, 0, 1)]
#     else:
#         raise Exception("Incorrect input type. Please enter `1` or `2`.")

#     standings.loc[matchup.home_team.team_id, "wins"] += home_outcome[0]  # type: ignore
#     standings.loc[matchup.home_team.team_id, "losses"] += home_outcome[2]  # type: ignore
#     standings.loc[matchup.away_team.team_id, "wins"] += away_outcome[0]  # type: ignore
#     standings.loc[matchup.away_team.team_id, "losses"] += away_outcome[2]  # type: ignore
