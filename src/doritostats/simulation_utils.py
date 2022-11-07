import numpy as np
from espn_api.football import League, Team
from doritostats.fetch_utils import PseudoMatchup


def get_score_prediction(team: Team):
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
