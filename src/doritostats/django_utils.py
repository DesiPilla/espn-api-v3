from espn_api.football import League
from src.doritostats.analytic_utils import (
    sort_lineups_by_func,
    get_best_lineup,
    get_best_trio,
    get_lineup_efficiency,
    avg_slot_score,
    sum_bench_points,
    get_season_luck_indices
)

''' DJANGO WEB FUNCTIONS '''
def django_weekly_stats(league: League):
    # Load box scores for specified week
    week = league.current_week - 1
    box_scores = league.box_scores(week)

    best_table = [
        ['Most Points Scored: ', sorted(
            league.teams, key=lambda x:x.scores[week-1], reverse=True)[0].owner],
        ['Best Possible Lineup: ', sort_lineups_by_func(
            league, week, get_best_lineup, box_scores)[-1].owner],
        ['Best Trio: ', sort_lineups_by_func(
            league, week, get_best_trio, box_scores)[-1].owner],
        ['Best Lineup Setter', sort_lineups_by_func(
            league, week, get_lineup_efficiency, box_scores)[-1].owner],
        ['Best QBs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='QB')[-1].owner],
        ['Best RBs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='RB')[-1].owner],
        ['Best WRs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='WR')[-1].owner],
        ['Best TEs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='TE')[-1].owner],
        ['Best Flex: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[-1].owner],
        ['Best DST: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot=r'D/ST')[-1].owner],
        ['Best K: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='K')[-1].owner],
        ['Best Bench:', sort_lineups_by_func(
            league, week, sum_bench_points, box_scores)[-1].owner]
    ]
    worst_table = [
        ['Least Points Scored: ', sorted(
            league.teams, key=lambda x:x.scores[week-1])[0].owner],
        ['---------------------', '----------------'],
        ['Worst Trio: ', sort_lineups_by_func(
            league, week, get_best_trio, box_scores)[0].owner],
        ['Worst Lineup Setter', sort_lineups_by_func(
            league, week, get_lineup_efficiency, box_scores)[0].owner],
        ['Worst QBs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='QB')[0].owner],
        ['Worst RBs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='RB')[0].owner],
        ['Worst WRs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='WR')[0].owner],
        ['Worst TEs: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='TE')[0].owner],
        ['Worst Flex: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[0].owner],
        ['Worst DST: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot=r'D/ST')[0].owner],
        ['Worst K: ', sort_lineups_by_func(
            league, week, avg_slot_score, box_scores, slot='K')[0].owner],
        ['Worst Bench:', sort_lineups_by_func(
            league, week, sum_bench_points, box_scores)[0].owner],
    ]

    weekly_stats = []
    for i in range(len(best_table)):
        weekly_stats.append({
            'best_label': best_table[i][0],
            'best_owner': best_table[i][1],
            'worst_label': worst_table[i][0],
            'worst_owner': worst_table[i][1]
        })

    return weekly_stats


def django_power_rankings(league: League):
    # Get power rankings for the current week
    league_power_rankings = league.power_rankings(league.current_week-1)

    # Add the power rankings for each team
    power_rankings = []
    for i in range(len(league_power_rankings)):
        power_rankings.append({
            'team': league_power_rankings[i][1].team_name,
            'value': league_power_rankings[i][0],
            'owner': league_power_rankings[i][1].owner
        })

    return power_rankings


def django_luck_index(league: League):
    # Get luck index for the current week
    league_luck_index = get_season_luck_indices(league, league.current_week-1)

    # Add the luck index for each team
    luck_index = []
    for (team, luck) in sorted(league_luck_index.items(), key=lambda x: x[1], reverse=True):
        luck_index.append({
            'team': team.team_name,
            'value': '{:.1f}'.format(luck),
            'owner': team.owner
        })

    return luck_index


def django_standings(league: League):
    # Get power rankings for the current week
    league_standings = league.standings()

    # Add the power rankings for each team
    standings = []
    for team in league_standings:
        standings.append({
            'team': team.team_name,
            'wins': team.wins,
            'losses': team.losses,
            'ties': team.ties,
            'points_for': '{:.1f}'.format(team.points_for),
            'owner': team.owner,
        })

    return standings