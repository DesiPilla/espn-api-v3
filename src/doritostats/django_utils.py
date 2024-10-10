import datetime
from typing import Dict, List, Optional, Tuple, Union
from espn_api.football import League

from fantasy_stats.models import LeagueInfo
from src.doritostats.analytic_utils import (
    get_num_active,
    get_remaining_schedule_difficulty_df,
    sort_lineups_by_func,
    get_best_lineup,
    get_best_trio,
    get_lineup_efficiency,
    avg_slot_score,
    sum_bench_points,
    get_score_surprise,
    get_total_tds,
)
from src.doritostats.luck_index import get_weekly_luck_index
from src.doritostats.simulation_utils import simulate_season


def ordinal(n: int) -> str:
    """This function returns the ordinal of a number.

    Ex: 1 -> 1st, 2 -> 2nd, 3 -> 3rd, 4 -> 4th, 5 -> 5th, etc.

    Args:
        n (int): The number to get the ordinal of.

    Returns:
        str: The ordinal of the number.
    """
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


def get_leagues_current_year():
    now = datetime.datetime.now()
    current_year = now.year if now.month >= 5 else now.year - 1

    return (
        LeagueInfo.objects.filter(league_year=current_year)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )


def get_leagues_previous_year():
    now = datetime.datetime.now()
    current_year = now.year if now.month >= 5 else now.year - 1

    return (
        LeagueInfo.objects.filter(league_year__lt=current_year)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )


def get_distinct_leagues_previous_year(
    leagues_current_year: Optional[List[LeagueInfo]] = None,
):
    if not leagues_current_year:
        leagues_current_year = get_leagues_current_year()

    distinct_leagues = (
        LeagueInfo.objects.filter().order_by("-league_id").distinct("league_id")
    )
    return [
        league_obj
        for league_obj in distinct_leagues
        if league_obj.league_id not in leagues_current_year
    ]


def django_weekly_stats(league: League, week: int):
    # Load box scores for specified week
    box_scores = league.box_scores(week)

    # Get the scores for each team
    team_scores = []
    for matchup in box_scores:
        team_scores.append((matchup.home_team, matchup.home_score))
        team_scores.append((matchup.away_team, matchup.away_score))
    team_scores

    best_table = [
        [
            "Most Points Scored: ",
            sorted(team_scores, key=lambda x: x[1], reverse=True)[0][0].owner,
        ],
        [
            "Best Possible Lineup: ",
            sort_lineups_by_func(league, week, get_best_lineup, box_scores)[-1].owner,
        ],
        [
            "Most TDs: ",
            sort_lineups_by_func(league, week, get_total_tds, box_scores)[-1].owner,
        ],
        [
            "Best Trio: ",
            sort_lineups_by_func(league, week, get_best_trio, box_scores)[-1].owner,
        ],
        [
            "Best Lineup Setter",
            sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[
                -1
            ].owner,
        ],
        [
            "Projection Outperformer:",
            sort_lineups_by_func(league, week, get_score_surprise, box_scores)[
                -1
            ].owner,
        ],
        [
            "Best QBs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="QB")[
                -1
            ].owner,
        ],
        [
            "Best RBs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="RB")[
                -1
            ].owner,
        ],
        [
            "Best WRs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="WR")[
                -1
            ].owner,
        ],
        [
            "Best TEs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="TE")[
                -1
            ].owner,
        ],
        [
            "Best Flex: ",
            sort_lineups_by_func(
                league, week, avg_slot_score, box_scores, slot=r"RB/WR/TE"
            )[-1].owner,
        ],
        [
            "Best DST: ",
            sort_lineups_by_func(
                league, week, avg_slot_score, box_scores, slot=r"D/ST"
            )[-1].owner,
        ],
        [
            "Best K: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="K")[
                -1
            ].owner,
        ],
        [
            "Best Bench:",
            sort_lineups_by_func(league, week, sum_bench_points, box_scores)[-1].owner,
        ],
        [
            "Fewest inactive players:",
            sort_lineups_by_func(league, week, get_num_active, box_scores)[-1].owner,
        ],
    ]
    worst_table = [
        [
            "Least Points Scored: ",
            sorted(team_scores, key=lambda x: x[1])[0][0].owner,
        ],
        [
            "Worst Optimal Lineup: ",
            sort_lineups_by_func(league, week, get_best_lineup, box_scores)[0].owner,
        ],
        [
            "Fewest TDs: ",
            sort_lineups_by_func(league, week, get_total_tds, box_scores)[0].owner,
        ],
        [
            "Worst Trio: ",
            sort_lineups_by_func(league, week, get_best_trio, box_scores)[0].owner,
        ],
        [
            "Worst Lineup Setter",
            sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[
                0
            ].owner,
        ],
        [
            "Projection Underperformer:",
            sort_lineups_by_func(league, week, get_score_surprise, box_scores)[0].owner,
        ],
        [
            "Worst QBs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="QB")[
                0
            ].owner,
        ],
        [
            "Worst RBs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="RB")[
                0
            ].owner,
        ],
        [
            "Worst WRs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="WR")[
                0
            ].owner,
        ],
        [
            "Worst TEs: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="TE")[
                0
            ].owner,
        ],
        [
            "Worst Flex: ",
            sort_lineups_by_func(
                league, week, avg_slot_score, box_scores, slot=r"RB/WR/TE"
            )[0].owner,
        ],
        [
            "Worst DST: ",
            sort_lineups_by_func(
                league, week, avg_slot_score, box_scores, slot=r"D/ST"
            )[0].owner,
        ],
        [
            "Worst K: ",
            sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot="K")[
                0
            ].owner,
        ],
        [
            "Worst Bench:",
            sort_lineups_by_func(league, week, sum_bench_points, box_scores)[0].owner,
        ],
        [
            "Most inactive players:",
            sort_lineups_by_func(league, week, get_num_active, box_scores)[0].owner,
        ],
    ]

    weekly_stats = []
    for i in range(len(best_table)):
        weekly_stats.append(
            {
                "best_label": best_table[i][0],
                "best_owner": best_table[i][1],
                "worst_label": worst_table[i][0],
                "worst_owner": worst_table[i][1],
            }
        )

    return weekly_stats


def django_power_rankings(league: League, week: int):
    # Get power rankings for the current week
    league_power_rankings = league.power_rankings(week)

    # Add the power rankings for each team
    power_rankings = []
    for i in range(len(league_power_rankings)):
        power_rankings.append(
            {
                "team": league_power_rankings[i][1].team_name,
                "value": league_power_rankings[i][0],
                "owner": league_power_rankings[i][1].owner,
            }
        )

    return power_rankings


def django_luck_index(league: League, week: int):
    # Get luck index for the current week
    league_luck_index = [
        (team, get_weekly_luck_index(league, team, week)) for team in league.teams
    ]

    # Add the luck index for each team
    luck_index = []
    for team, luck in sorted(league_luck_index, key=lambda x: x[1], reverse=True):
        if luck >= 0:
            luck_val = "+{:.1%} luckiness this week".format(luck)
        else:
            luck_val = "{:.1%} unluckiness this week".format(luck)
        luck_index.append(
            {"team": team.team_name, "value": luck_val, "owner": team.owner}
        )

    return luck_index


def django_standings(league: League, week: int):
    # Get power rankings for the current week
    if week <= 1:
        # ZeroDivisionError if no games have meen completed yet
        league_standings = league.standings()
    else:
        league_standings = league.standings_weekly(week)

    # Add the power rankings for each team
    standings = []
    for team in league_standings:
        standings.append(
            {
                "team": team.team_name,
                "wins": sum([outcome == "W" for outcome in team.outcomes[:week]]),
                "losses": sum([outcome == "L" for outcome in team.outcomes[:week]]),
                "ties": sum([outcome == "T" for outcome in team.outcomes[:week]]),
                "points_for": "{:.1f}".format(sum(team.scores[:week])),
                "owner": team.owner,
            }
        )

    return standings


def django_strength_of_schedule(
    league: League, week: int
) -> Tuple[List[Dict[str, Union[str, float]]], Tuple[int, int]]:
    """This is a helper function to get the remaining strength of schedule for each team in the league.
    The results are returned as a list of dictionaries, which is the most conveneint format
    for django to render.

    Args:
        league (League): A formatted ESPN league object.
        week (int): First week to include as "remaining". I.e., week = 10 will calculate the remaining SOS for Weeks 10 -> end of season.

    Returns:
        List[Dict[str, Union[str, float]]]: List of dictionaries containing the strength of schedule for each team
        Tuple[int, int]: Tuple containing the range of weeks defining a team's remaining schedule
            * For example, if the SOS for Week 6 and beyond is desired, this tuple would be (6, regular_season_length)
    """
    # Get strength of schedule for the current week
    sos_df, _, schedule_period = get_remaining_schedule_difficulty_df(league, week)

    # Add the strength of schedule for each team
    django_sos = []
    for i in range(len(sos_df)):
        django_sos.append(
            {
                "team": sos_df.iloc[i].name.team_name,
                "opp_points_for": "{:.1f}".format(sos_df.iloc[i].opp_points_for),
                "opp_win_pct": "{:.3f}".format(sos_df.iloc[i].opp_win_pct),
                "opp_power_rank": "{:.1f}".format(sos_df.iloc[i].opp_power_rank),
                "overall_difficulty": "{:.1f}".format(
                    sos_df.iloc[i].overall_difficulty
                ),
                "owner": sos_df.iloc[i].name.owner,
            }
        )

    return django_sos, schedule_period


def django_simulation(league: League, n_simulations: int):
    if league.current_week >= league.settings.reg_season_count:
        n_simulations = 1

    # Get power rankings for the current week
    playoff_odds, rank_dist, seeding_outcomes = simulate_season(league, n=n_simulations)

    # Add the playoff offs and final rank distribution for each team
    django_playoff_odds = []
    django_rank_dist = []
    django_seeding_outcomes = []
    for i in range(len(playoff_odds)):
        # Add the odds of making the playoffs for this team
        django_playoff_odds.append(
            {
                "team": playoff_odds.iloc[i].team_name,
                "owner": playoff_odds.iloc[i].team_owner,
                "projected_wins": playoff_odds.iloc[i].wins,
                "projected_losses": playoff_odds.iloc[i].losses,
                "projected_ties": playoff_odds.iloc[i].ties,
                "projected_points_for": "{:.1f}".format(
                    playoff_odds.iloc[i].points_for
                ),
                "playoff_odds": "{:.1f}%".format(playoff_odds.iloc[i].playoff_odds),
            }
        )

        # Add the odds of finishing in each position this team
        rank_cols = [c for c in rank_dist.columns if type(c) == int]
        django_rank_dist.append(
            {
                "team": rank_dist.iloc[i].team_name,
                "owner": rank_dist.iloc[i].team_owner,
                "position_odds": [
                    "{:.1%}".format(rank_dist.iloc[i][c] / 100) for c in rank_cols
                ],
                "playoff_odds": "{:.1f}%".format(rank_dist.iloc[i].playoff_odds),
            }
        )

        # Add the odds of each seeding outcome for this team
        django_seeding_outcomes.append(
            {
                "team": seeding_outcomes.iloc[i].team_name,
                "owner": seeding_outcomes.iloc[i].team_owner,
                "first_in_league": "{:.1%}".format(
                    seeding_outcomes.iloc[i].first_in_league / 100
                ),
                "first_in_division": "{:.1%}".format(
                    seeding_outcomes.iloc[i].first_in_division / 100
                ),
                "make_playoffs": "{:.1f}%".format(
                    seeding_outcomes.iloc[i].make_playoffs
                ),
                "last_in_division": "{:.1%}".format(
                    seeding_outcomes.iloc[i].last_in_division / 100
                ),
                "last_in_league": "{:.1%}".format(
                    seeding_outcomes.iloc[i].last_in_league / 100
                ),
            }
        )

    return django_playoff_odds, django_rank_dist, django_seeding_outcomes
