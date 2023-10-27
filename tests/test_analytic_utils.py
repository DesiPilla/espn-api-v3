import pytest
import inspect
from typing import Callable
from espn_api.football import League, Team

from src.doritostats.fetch_utils import fetch_league
import src.doritostats.analytic_utils as utils  # The code to test

import os
from dotenv import load_dotenv

load_dotenv("../.env", override=True)

league_id = os.getenv("LEAGUE_ID")
swid = os.getenv("SWID")
espn_s2 = os.getenv("ESPN_S2")

league_2018 = fetch_league(league_id=league_id, year=2018, swid=swid, espn_s2=espn_s2)
league_2022 = fetch_league(league_id=league_id, year=2022, swid=swid, espn_s2=espn_s2)

team_2018_2 = league_2018.teams[2]
team_2022_0 = league_2022.teams[0]
team_2022_5 = league_2022.teams[5]
box_scores_2022_4 = league_2022.box_scores(4)
lineup_2022_t0_w1 = utils.get_lineup(league_2022, team_2022_0, 1)
lineup_2022_t5_w4 = utils.get_lineup(league_2022, team_2022_5, 4)


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
def test_get_top_players(lineup: list, slot: str, n: int, results: list):
    top_players = utils.get_top_players(lineup, slot, n)
    player_names = [player.name for player in top_players]
    assert player_names == results


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 128.0), (league_2022, lineup_2022_t5_w4, 196.52)],
)
def test_get_best_lineup(league: League, lineup: list, result: float):
    assert utils.get_best_lineup(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 61.0), (league_2022, lineup_2022_t5_w4, 85.92)],
)
def test_get_best_trio(league: League, lineup: list, result: float):
    assert utils.get_best_trio(league, lineup) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [
        (league_2022, lineup_2022_t0_w1, 0.8242),
        (league_2022, lineup_2022_t5_w4, 0.5734),
    ],
)
def test_get_lineup_efficiency(league: League, lineup: list, result: float):
    assert pytest.approx(utils.get_lineup_efficiency(league, lineup), 0.0001) == result


@pytest.mark.parametrize(
    "league, team, week, result",
    [(league_2022, team_2022_0, 1, 9), (league_2022, team_2022_5, 4, 6)],
)
def test_get_weekly_finish(league: League, team: Team, week: int, result: int):
    assert utils.get_weekly_finish(league, team, week) == result


# @pytest.mark.parametrize(", result", [()])
# def test_get_num_out(result: int):
#     assert utils.get_num_out() == result


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
def test_avg_slot_score(league: League, lineup: list, slot: str, result: float):
    assert pytest.approx(utils.avg_slot_score(league, lineup, slot), 0.01) == result


@pytest.mark.parametrize(
    "league, lineup, result",
    [(league_2022, lineup_2022_t0_w1, 55.7), (league_2022, lineup_2022_t5_w4, 124.62)],
)
def test_sum_bench_points(league: League, lineup: list, result: float):
    assert utils.sum_bench_points(league, lineup) == result


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
