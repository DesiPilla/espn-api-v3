import numpy as np
from espn_api.football import League, Team
from doritostats.fetch_utils import PseudoMatchup


def get_score_prediction(team: Team):
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


    scores = np.array(team.scores)
    scores = scores[scores > 0][-6:]
    return np.random.normal(scores.mean(), scores.std())


def predict_matchup(matchup: PseudoMatchup):
    home_score = get_score_prediction(matchup.home_team)
    away_score = get_score_prediction(matchup.away_team)

    # No ties
    if away_score > home_score:
        return (0, 1)
    else:
        return (1, 0)
