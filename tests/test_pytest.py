import pytest
import pandas as pd
from espn_api.football import League, Team, Matchup
import src.doritostats.fetch_utils as fetch   # The code to test

# Import example creds
login = pd.read_csv('./login.csv')
_, _, league_id, swid, espn_s2 = login.iloc[0]
league_2018 = fetch.fetch_league(league_id, 2018, swid, espn_s2)
league_2022 = fetch.fetch_league(league_id, 2022, swid, espn_s2)

@pytest.mark.parametrize("league, endpoint",
                         [(league_2018, "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/1086064?seasonId=2018&"),
                          (league_2022, "https://fantasy.espn.com/apis/v3/games/ffl/seasons/2022/segments/0/leagues/1086064?")])
def test_set_league_endpoint(league: League, endpoint: str):
    fetch.set_league_endpoint(league)
    assert league.endpoint == endpoint
    
    
@pytest.mark.parametrize("league_id, year, swid, espn_s2, results",
                         [
                             (league_id, 2018, swid, espn_s2,
                              {
                                  "league_name":"Make Football Great Again",
                                  "cookies":{'swid': swid, 'espn_s2': espn_s2},
                                }),
                             (league_id, 2022, swid, espn_s2,
                              {
                                  "league_name": "La Lega dei Cugini",
                                  "cookies": {'swid': swid, 'espn_s2': espn_s2}
                              })
                         ])
def test_fetch_league(league_id: int, year: int, swid: str, espn_s2: str, results: dict):
    league = fetch.fetch_league(league_id, year, swid, espn_s2)
    assert league.name == results['league_name']
    assert league.cookies == results['cookies']


@pytest.mark.parametrize("league, matchup, week, result",
                         [
                             (league_2018, fetch.PseudoMatchup(
                                 league_2018.teams[0], league_2018.teams[0].schedule[0]), 1, False), # Regular season
                             (league_2018, fetch.PseudoMatchup(
                                 league_2018.teams[0], league_2018.teams[0].schedule[12]), 13, True), # Known playoff game
                             (league_2018, fetch.PseudoMatchup(
                                 league_2018.teams[5], league_2018.teams[5].schedule[12]), 13, False), # Known consolation game
                             (league_2022, league_2022.box_scores(
                                 1)[0], 1, False), # Regular season
                             (league_2022, league_2022.box_scores(
                                 15)[0], 15, True), # Playoff game
                             (league_2022, league_2022.box_scores(15)
                              [-1], 15, False), # Consolation game
                          ])
def test_is_playoff_game(league: League, matchup: Matchup, week: int, result: bool):
    assert fetch.is_playoff_game(league, matchup, week) == result