from src.doritostats.simulation_utils import simulate_season
from espn_api.football import League
from .analytic_utils import (
    sort_lineups_by_func,
    get_best_lineup,
    get_best_trio,
    get_lineup_efficiency,
    avg_slot_score,
    sum_bench_points,
    get_score_surprise,
    get_season_luck_indices,
    get_total_tds,
)


def django_weekly_stats(league: League, week: int):
    # Load box scores for specified week
    box_scores = league.box_scores(week)

    best_table = [
        [
            "Most Points Scored: ",
            sorted(league.teams, key=lambda x: x.scores[week - 1], reverse=True)[
                0
            ].owner,
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
    ]
    worst_table = [
        [
            "Least Points Scored: ",
            sorted(league.teams, key=lambda x: x.scores[week - 1])[0].owner,
        ],
        ["---------------------", "----------------"],
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
    league_luck_index = get_season_luck_indices(league, week)

    # Add the luck index for each team
    luck_index = []
    for team, luck in sorted(
        league_luck_index.items(), key=lambda x: x[1], reverse=True
    ):
        if luck >= 0:
            luck_val = "+{:.1f} net wins gained by luck".format(luck)
        else:
            luck_val = "{:.1f} net wins lost by unluckiness".format(luck)
        luck_index.append(
            {
                "team": team.team_name,
                "value": luck_val,
                "owner": team.owner,
            }
        )

    return luck_index


def django_standings(league: League):
    # Get power rankings for the current week
    league_standings = league.standings()

    # Add the power rankings for each team
    standings = []
    for team in league_standings:
        standings.append(
            {
                "team": team.team_name,
                "wins": team.wins,
                "losses": team.losses,
                "ties": team.ties,
                "points_for": "{:.1f}".format(team.points_for),
                "owner": team.owner,
            }
        )

    return standings


def django_simulation(league: League):
    # Get power rankings for the current week
    playoff_odds = simulate_season(league, n=500)

    # Add the power rankings for each team
    django_playoff_odds = []
    for i in range(len(playoff_odds)):
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
                "playoff_odds": "{:.1%}".format(
                    playoff_odds.iloc[i].playoff_odds / 100
                ),
            }
        )

    return django_playoff_odds
