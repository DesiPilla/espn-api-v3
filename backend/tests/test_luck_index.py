import pytest
import src.doritostats.luck_index as luck  # The code to test
from typing import List


# luck.calculate_scheduling_factor -- TODO
# luck.get_injury_bye_factor -- TODO
# luck.get_performance_vs_projection_factor -- TODO
# luck.get_optimal_vs_actual_factor -- TODO
# luck.get_optimal_vs_optimal_factor -- TODO


@pytest.mark.parametrize(
    "team_score, team_scores, result",
    [
        (100, [105, 110, 90, 95], 0),
        (90, [105, 110, 90, 95], -0.63),
        (110, [105, 110, 90, 95], 0.63),
        (80, [105, 110, 90, 95], -1),
        (120, [105, 110, 90, 95], 1),
    ],
)
def test_calculate_performance_vs_historical_average(
    team_score: float, team_scores: List[float], result: float
):
    assert luck.calculate_performance_vs_historical_average(
        team_score, team_scores
    ) == pytest.approx(result, 0.01)


@pytest.mark.parametrize(
    "team_score, opp_score, result",
    [
        (100, 110, -0.5),
        (110, 100, 0.5),
        (100, 50, 0),
        (50, 100, 0),
        (100, 101, -0.95),
        (101, 100, 0.95),
    ],
)
def test_calculate_margin_of_victory_factor(
    team_score: float, opp_score: float, result: float
):
    assert luck.calculate_margin_of_victory_factor(team_score, opp_score) == result
