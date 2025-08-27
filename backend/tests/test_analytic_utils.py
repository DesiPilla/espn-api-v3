import inspect
import os
import numpy as np
import pytest
from typing import Callable, List, Optional

from espn_api.football import League, Team, Player

from backend.src.doritostats.fetch_utils import fetch_league
import src.doritostats.analytic_utils as utils  # The code to test


league_id = os.getenv("LEAGUE_ID")
swid = os.getenv("SWID")
espn_s2 = os.getenv("ESPN_S2")

league_2018 = fetch_league(league_id=league_id, year=2018, swid=swid, espn_s2=espn_s2)
league_2020 = fetch_league(league_id=league_id, year=2020, swid=swid, espn_s2=espn_s2)
league_2021 = fetch_league(league_id=league_id, year=2021, swid=swid, espn_s2=espn_s2)
league_2022 = fetch_league(league_id=league_id, year=2022, swid=swid, espn_s2=espn_s2)
league_2023 = fetch_league(league_id=league_id, year=2023, swid=swid, espn_s2=espn_s2)

team_2018_2 = league_2018.teams[2]
team_2020_0 = league_2020.teams[0]
team_2021_0 = league_2021.teams[0]
team_2022_0 = league_2022.teams[0]
team_2022_5 = league_2022.teams[5]
team_2023_0 = league_2023.teams[0]
box_scores_2022_4 = league_2022.box_scores(4)
lineup_2020_t0_w15 = utils.get_lineup(league_2020, team_2020_0, 15)
lineup_2022_t0_w1 = utils.get_lineup(league_2022, team_2022_0, 1)
lineup_2022_t5_w4 = utils.get_lineup(league_2022, team_2022_5, 4)
lineup_2023_t0_w2 = utils.get_lineup(league_2023, league_2023.teams[0], 2)
lineup_2023_t0_w5 = utils.get_lineup(league_2023, league_2023.teams[0], 5)
lineup_2023_t0_w8 = utils.get_lineup(league_2023, league_2023.teams[0], 8)
lineup_2023_t0_w10 = utils.get_lineup(league_2023, league_2023.teams[0], 10)
lineup_2023_t7_w7 = utils.get_lineup(league_2023, league_2023.teams[7], 7)


@pytest.mark.parametrize(
    "league, team, week, box_scores, results",
    [
        # Before 2019, cannot get lineup
        (league_2018, team_2018_2, 1, None, None),
        # Contains IR player
        (
            league_2022,
            team_2022_0,
            1,
            None,
            {
                "len": 19,
                "player_names": [
                    "Najee Harris",
                    "Travis Kelce",
                    "Keenan Allen",
                    "Travis Etienne Jr.",
                    "Breece Hall",
                    "Courtland Sutton",
                    "Christian Kirk",
                    "Russell Wilson",
                    "DeVonta Smith",
                    "Cordarrelle Patterson",
                    "Allen Lazard",
                    "Matthew Stafford",
                    "George Pickens",
                    "Alexander Mattison",
                    "Brian Robinson Jr.",
                    "Isaiah McKenzie",
                    "Tyler Bass",
                    "Browns D/ST",
                    "Jerick McKinnon",
                ],
            },
        ),
        # No IR player, weekly roster != from drafted roster
        (
            league_2022,
            team_2022_5,
            4,
            None,
            {
                "len": 18,
                "player_names": [
                    "Austin Ekeler",
                    "Deebo Samuel",
                    "Aaron Jones",
                    "George Kittle",
                    "Josh Jacobs",
                    "Amon-Ra St. Brown",
                    "Joe Burrow",
                    "Amari Cooper",
                    "Miles Sanders",
                    "Rashod Bateman",
                    "Justin Tucker",
                    "Chris Olave",
                    "Saints D/ST",
                    "Julio Jones",
                    "Tyler Allgeier",
                    "Chargers D/ST",
                    "Albert Okwuegbunam",
                    "Jared Goff",
                ],
            },
        ),
        # Using BoxScore (Week 4)
        (
            league_2022,
            team_2022_5,
            4,
            box_scores_2022_4,
            {
                "len": 18,
                "player_names": [
                    "Austin Ekeler",
                    "Deebo Samuel",
                    "Aaron Jones",
                    "George Kittle",
                    "Josh Jacobs",
                    "Amon-Ra St. Brown",
                    "Joe Burrow",
                    "Amari Cooper",
                    "Miles Sanders",
                    "Rashod Bateman",
                    "Justin Tucker",
                    "Chris Olave",
                    "Saints D/ST",
                    "Julio Jones",
                    "Tyler Allgeier",
                    "Chargers D/ST",
                    "Albert Okwuegbunam",
                    "Jared Goff",
                ],
            },
        ),
    ],
)
def test_get_lineup(league: League, team: Team, week: int, box_scores, results: dict):
    if league.year < 2019:
        with pytest.raises(Exception):
            assert utils.get_lineup(league, team, week, box_scores), Exception(
                "Cant use box score before 2019"
            )
    else:
        lineup = utils.get_lineup(league, team, week, box_scores)
        player_names = [player.name for player in lineup]
        assert len(lineup) == results["len"]
        assert all(player in player_names for player in results["player_names"])


@pytest.mark.parametrize(
    "lineup, slot, n, results",
    [
        (lineup_2022_t0_w1, "QB", 1, ["Russell Wilson"]),
        (lineup_2022_t0_w1, "RB", 2, ["Cordarrelle Patterson", "Najee Harris"]),
        (
            lineup_2022_t0_w1,
            "WR",
            3,
            ["Christian Kirk", "Courtland Sutton", "Isaiah McKenzie"],
        ),
        # Select top 2, but there is only 1 TE
        (lineup_2022_t0_w1, "TE", 2, ["Travis Kelce"]),
        (lineup_2022_t5_w4, "RB/WR/TE", 2, ["Josh Jacobs", "Austin Ekeler"]),
        (lineup_2022_t5_w4, "D/ST", 1, ["Chargers D/ST"]),
        (lineup_2022_t5_w4, "K", 2, ["Justin Tucker"]),
    ],
)
def test_get_top_players(lineup: List[Player], slot: str, n: int, results: list):
    top_players = utils.get_top_players(lineup, slot, n)
    player_names = [player.name for player in top_players]
    assert player_names == results


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 128.0), (league_2022, lineup_2022_t5_w4, 196.52)],
)
def test_get_best_lineup(league: League, lineup: List[Player], result: float):
    assert utils.get_best_lineup(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 61.0), (league_2022, lineup_2022_t5_w4, 85.92)],
)
def test_get_best_trio(league: League, lineup: List[Player], result: float):
    assert utils.get_best_trio(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [
        (league_2022, lineup_2022_t0_w1, 0.8242),
        (league_2022, lineup_2022_t5_w4, 0.5734),
    ],
)
def test_get_lineup_efficiency(league: League, lineup: List[Player], result: float):
    assert pytest.approx(utils.get_lineup_efficiency(league, lineup), 0.0001) == result


@pytest.mark.parametrize(
    "league, team, week, result",
    [(league_2022, team_2022_0, 1, 9), (league_2022, team_2022_5, 4, 6)],
)
def test_get_weekly_finish(league: League, team: Team, week: int, result: int):
    assert utils.get_weekly_finish(league, team, week) == result


@pytest.mark.parametrize(
    "lineup, result",
    [
        (lineup_2020_t0_w15, 10),
        (lineup_2023_t0_w2, 17),
        (lineup_2023_t0_w5, 17),
        (lineup_2023_t0_w8, 18),
        (lineup_2023_t0_w10, 14),
        (lineup_2023_t7_w7, 10),
    ],
)
def test_get_num_active(
    lineup: List[Player],
    result: int,
):
    assert utils.get_num_active(None, lineup) == result


@pytest.mark.parametrize(
    "lineup, result",
    [
        (lineup_2020_t0_w15, 0),
        (lineup_2023_t0_w2, 1),
        (lineup_2023_t0_w5, 1),
        (lineup_2023_t0_w8, 0),
        (lineup_2023_t0_w10, 1),
        (lineup_2023_t7_w7, 2),
    ],
)
def test_get_num_inactive(
    lineup: List[Player],
    result: int,
):
    assert utils.get_num_inactive(None, lineup) == result


@pytest.mark.parametrize(
    "lineup, result",
    [
        (lineup_2020_t0_w15, 0),
        (lineup_2023_t0_w2, 0),
        (lineup_2023_t0_w5, 0),
        (lineup_2023_t0_w8, 0),
        (lineup_2023_t0_w10, 3),
        (lineup_2023_t7_w7, 6),
    ],
)
def test_get_num_bye(
    lineup: List[Player],
    result: int,
):
    assert utils.get_num_bye(None, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, slot, result",
    [
        (league_2022, lineup_2022_t0_w1, "QB", 17.8),
        (league_2022, lineup_2022_t0_w1, "RB", 8.55),
        (league_2022, lineup_2022_t0_w1, "WR", 8.9),
        (league_2022, lineup_2022_t0_w1, "TE", 22.1),
        (league_2022, lineup_2022_t5_w4, "RB/WR/TE", 2.3),
        (league_2022, lineup_2022_t5_w4, "D/ST", 8.0),
        (league_2022, lineup_2022_t5_w4, "K", 11.0),
    ],
)
def test_avg_slot_score(league: League, lineup: List[Player], slot: str, result: float):
    assert pytest.approx(utils.avg_slot_score(league, lineup, slot), 0.01) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 55.7), (league_2022, lineup_2022_t5_w4, 124.62)],
)
def test_sum_bench_points(league: League, lineup: List[Player], result: float):
    assert utils.sum_bench_points(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [
        (league_2022, lineup_2022_t0_w1, 115.09),
        (league_2022, lineup_2022_t5_w4, 110.38),
    ],
)
def test_get_projected_score(league: League, lineup: List[Player], result: float):
    assert utils.get_projected_score(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [
        (league_2022, lineup_2022_t0_w1, -9.59),
        (league_2022, lineup_2022_t5_w4, 2.3),
    ],
)
def test_get_score_surprise(league: League, lineup: List[Player], result: float):
    assert pytest.approx(utils.get_score_surprise(league, lineup), 0.01) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [
        (league_2022, lineup_2022_t0_w1, 3),
        (league_2022, lineup_2022_t5_w4, 6),
    ],
)
def test_get_total_tds(league: League, lineup: List[Player], result: float):
    assert utils.get_total_tds(league, lineup) == result


@pytest.mark.parametrize(
    "outcomes, result",
    [
        (team_2018_2.outcomes[:1], 0.0000),  # 0-1-0
        (team_2018_2.outcomes[:10], 0.4000),  # 4-6-0
        # TODO: Uncomment when Ties are implemented in espn-api
        # (team_2021_0.outcomes[:7], 0.2857),  # 2-5-0
        # (team_2021_0.outcomes[:8], 0.2857),  # 2-5-1
        ([], 0),  # Season hasn't started
        (team_2023_0.outcomes[:1], 1.0000),  # 1-0-0
        (team_2023_0.outcomes[:10], 0.5000),  # 5-5-0
    ],
)
def test_calculate_win_pct(outcomes: List[str], result: float):
    assert pytest.approx(utils.calculate_win_pct(np.array(outcomes)), 0.0001) == result


@pytest.mark.parametrize(
    "team, week, regular_season_length, strength, league, result",
    [
        (team_2023_0, 11, 14, "points_for", None, 116.8479),
        (team_2023_0, 12, 14, "points_for", None, 120.0408),
        (team_2023_0, 13, 14, "points_for", None, 125.1508),
        (team_2023_0, 14, 14, "points_for", None, 0),
        (team_2023_0, 15, 14, "points_for", None, 0),
        (team_2023_0, 11, 14, "win_pct", None, 0.4545),
        (team_2023_0, 12, 14, "win_pct", None, 0.5417),
        (team_2023_0, 13, 14, "win_pct", None, 0.5385),
        (team_2023_0, 14, 14, "win_pct", None, 0),
        (team_2023_0, 15, 14, "win_pct", None, 0),
        (team_2023_0, 11, 14, "power_rank", league_2023, 42.3500),
        (team_2023_0, 12, 14, "power_rank", league_2023, 52.7750),
        (team_2023_0, 13, 14, "power_rank", league_2023, 56.8000),
        (team_2023_0, 14, 14, "power_rank", league_2023, 0),
        (team_2023_0, 15, 14, "power_rank", league_2023, 0),
    ],
)
def test_get_remaining_schedule_difficulty(
    team: Team,
    week: int,
    regular_season_length: int,
    strength: str,
    league: Optional[League],
    result: float,
):
    assert (
        pytest.approx(
            utils.get_remaining_schedule_difficulty(
                team, week, regular_season_length, strength, league
            )[0],
            0.0001,
        )
        == result
    )


@pytest.mark.parametrize(
    "league, week, func, box_scores, slot, result",
    [
        (
            league_2022,
            1,
            utils.get_best_lineup,
            None,
            None,
            [6, 8, 10, 1, 4, 5, 2, 7, 3, 9],
        ),
        (
            league_2022,
            4,
            utils.get_best_trio,
            None,
            None,
            [5, 7, 3, 1, 2, 10, 9, 8, 4, 6],
        ),
        (
            league_2022,
            4,
            utils.get_lineup_efficiency,
            box_scores_2022_4,
            None,
            [6, 10, 1, 3, 9, 4, 7, 2, 5, 8],
        ),
        (
            league_2022,
            1,
            utils.avg_slot_score,
            None,
            "QB",
            [8, 5, 1, 6, 2, 4, 10, 3, 7, 9],
        ),
        (
            league_2022,
            1,
            utils.avg_slot_score,
            None,
            "RB",
            [2, 1, 6, 7, 9, 10, 5, 8, 4, 3],
        ),
        (
            league_2022,
            1,
            utils.sum_bench_points,
            None,
            None,
            [8, 7, 1, 6, 2, 5, 3, 10, 4, 9],
        ),
    ],
)
def test_sort_lineups_by_func(
    league: League, week: int, func: Callable, box_scores: list, slot: str, result: int
):
    if "slot" in inspect.getfullargspec(func).args:
        sorted_teams = utils.sort_lineups_by_func(
            league, week, func, box_scores, slot=slot
        )
    else:
        sorted_teams = utils.sort_lineups_by_func(league, week, func, box_scores)
    sorted_team_ids = [team.team_id for team in sorted_teams]
    assert sorted_team_ids == result
