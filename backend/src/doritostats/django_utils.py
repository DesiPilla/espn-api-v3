import datetime
from typing import Dict, List, Optional, Tuple, Union
from espn_api.football import League

from backend.fantasy_stats.models import LeagueInfo
from backend.src.doritostats.analytic_utils import (
    avg_slot_score,
    get_best_lineup,
    get_best_trio,
    get_lineup_efficiency,
    get_num_active,
    get_remaining_schedule_difficulty_df,
    get_score_surprise,
    get_total_tds,
    season_stats_analysis,
    sort_lineups_by_func,
    sum_bench_points,
)
from backend.src.doritostats.luck_index import get_weekly_luck_index
from backend.src.doritostats.scrape_team_stats import (
    append_streaks,
    get_stats_by_matchup,
)
from backend.src.doritostats.simulation_utils import simulate_season

CURRENT_YEAR = (
    datetime.datetime.now().year
    if datetime.datetime.now().month >= 4
    else datetime.datetime.now().year - 1
)


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
    return (
        LeagueInfo.objects.filter(league_year=CURRENT_YEAR)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )


def get_leagues_previous_year():
    return (
        LeagueInfo.objects.filter(league_year__lt=CURRENT_YEAR)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )


def django_weekly_stats(league: League, week: int):
    # Load box scores for specified week
    box_scores = league.box_scores(week)

    # Get the scores for each team
    team_scores = []
    for matchup in box_scores:
        if not (matchup.home_team and matchup.away_team):
            # Skip byes
            continue
        team_scores.append((matchup.home_team, matchup.home_score))
        team_scores.append((matchup.away_team, matchup.away_score))

    # Calculate the best and worst awards
    best_awards = [
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
    worst_awards = [
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

    return best_awards, worst_awards


def django_season_stats(league: League):
    # Get the season stats
    df_year = get_stats_by_matchup(league=league)

    # Get win streak data for each owner
    df_year = append_streaks(df_year)
    df_year["box_score_available"] = True

    # Properly cast boolean columns to bool
    bool_cols = {
        col: bool for col in df_year.columns[df_year.columns.str.contains("is_")]
    }
    df_year = df_year.astype(bool_cols)

    # Get season records
    season_stats_dict = season_stats_analysis(
        league=league,
        df=df_year,
    )

    best_team_stats_dict = {
        "most_wins": "Most wins",
        "highest_single_game_score": "Highest game score",
        "longest_win_streak": "Longest win streak",
        "highest_avg_pts": "Most Points For",
        "highest_avg_pts_against": "Highest Points Against",
        "highest_single_game_score_dif": "Largest margin of victory",
        "highest_single_game_pts_surprise": "Largest projection beat",
        "highest_avg_lineup_efficiency": "Highest average lineup efficiency",
    }
    worst_team_stats_dict = {
        "most_losses": "Most losses",
        "lowest_single_game_score": "Lowest game score",
        "longest_loss_streak": "Longest loss streak",
        "lowest_avg_pts": "Fewest Points For",
        "lowest_avg_pts_against": "Fewest Points Against",
        "lowest_single_game_score_dif": "Biggest loss",
        "lowest_single_game_pts_surprise": "Biggest underperformance",
        "lowest_avg_lineup_efficiency": "Lowest average lineup efficiency",
    }
    best_position_stats_dict = {
        "most_QB_pts": "Most QB points",
        "most_RB_pts": "Most RB points",
        "most_WR_pts": "Most WR points",
        "most_TE_pts": "Most TE points",
        "most_RB_WR_TE_pts": "Most FLEX points",
        "most_D_ST_pts": "Most D/ST points",
        "most_K_pts": "Most K points",
        "most_bench_points": "Most Bench points",
    }
    worst_position_stats_dict = {
        "least_QB_pts": "Fewest QB points",
        "least_RB_pts": "Fewest RB points",
        "least_WR_pts": "Fewest WR points",
        "least_TE_pts": "Fewest TE points",
        "least_RB_WR_TE_pts": "Fewest FLEX points",
        "least_D_ST_pts": "Fewest D/ST points",
        "least_K_pts": "Fewest K points",
        "least_bench_points": "Fewest Bench points",
    }

    # Define lists for contain each set of stats
    best_team_stats_list = []
    worst_team_stats_list = []
    best_position_stats_list = []
    worst_position_stats_list = []
    stat_lists = [
        (best_team_stats_list, best_team_stats_dict),
        (worst_team_stats_list, worst_team_stats_dict),
        (best_position_stats_list, best_position_stats_dict),
        (worst_position_stats_list, worst_position_stats_dict),
    ]

    # Add the best and worst stats to the season stats list
    for stat_list, stat_dict in stat_lists:
        for stat_key, stat_label in stat_dict.items():
            # Format the best and worst stats
            stat = season_stats_dict[stat_key]
            stat_value = (
                stat["val_format"].format(stat["val"]) + " " + stat["val_units"]
            )

            # Add the best and worst stats to the season stats list
            stat_list.append(
                {
                    "label": stat_label,
                    "owner": stat["owners"],
                    "value": stat_value,
                }
            )

    return (
        best_team_stats_list,
        worst_team_stats_list,
        best_position_stats_list,
        worst_position_stats_list,
    )


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

    return sorted(power_rankings, key=lambda x: x["value"], reverse=True)


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
            {"team": team.team_name, "text": luck_val, "owner": team.owner, "value": luck}
        )

    return sorted(luck_index, key=lambda x: x["value"], reverse=True)


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
                "pointsFor": "{:.1f}".format(sum(team.scores[:week])),
                "owner": team.owner,
                # TODO: Add an indicator for playoff teams
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
    sos_df, _, schedule_period = get_remaining_schedule_difficulty_df(
        league=league, week=week
    )

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


def django_simulation(league: League, n_simulations: int, week: Optional[int] = None):
    # Disallow simulations after the regular season has ended
    # if league.current_week > league.settings.reg_season_count:
    #     n_simulations = 1

    # Get power rankings for the current week
    playoff_odds, rank_dist, seeding_outcomes = simulate_season(
        league, n=n_simulations, first_week_to_simulate=week
    )

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
