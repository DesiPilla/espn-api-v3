import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from espn_api.football import League, Team, Player

from copy import copy
from collections import Counter
from tabulate import tabulate as table


# Get a dictionary of the starting roster slots and number of each for the League (Week 1 must have passed already)
starting_roster_slots = Counter([p.slot_position for p in league.box_scores(1)[0].home_lineup if p.slot_position not in ['BE', 'IR']])


''' ANALYTIC FUNCTIONS '''

def get_lineup(league: League, team: Team, week: int, box_scores=None):
    ''' Return the lineup of the given team during the given week '''
    # Get the lineup for the team during the specified week
    if box_scores is None: box_scores = league.box_scores(week)
    for box_score in box_scores:
        if team == box_score.home_team:
            return box_score.home_lineup
        elif team == box_score.away_team:
            return box_score.away_lineup

def get_top_players(lineup: list, slot: str, n: int):
    ''' Takes a list of players and returns a list of the top n players based on points scored. '''
    # Gather players of the desired position
    eligible_players = []
    for player in lineup:
        if slot in player.eligibleSlots:
            eligible_players.append(player)
            
    return sorted(eligible_players, key=lambda x: x.points, reverse=True)[:n]


def get_best_lineup(lineup: list):
    ''' Returns the best possible lineup for team during the loaded week. '''
    # Save full roster
    saved_roster = copy(lineup)
    
    # Find Best Lineup
    best_lineup = []
    for slot in sorted(starting_roster_slots.keys(), key=len):  # Get best RB before best RB/WR/TE
        num_players = starting_roster_slots[slot]
        best_players = get_top_players(saved_roster, slot, num_players)
        best_lineup.extend(best_players)
        
        # Remove selected players from consideration for other slots
        for player in best_players:
            saved_roster.remove(player)

    return np.sum([player.points for player in best_lineup])


def get_best_trio(lineup: list):
    ''' Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week. '''
    qb = get_top_players(lineup, 'QB', 1)[0].points
    rb = get_top_players(lineup, 'RB', 1)[0].points
    wr = get_top_players(lineup, 'WR', 1)[0].points
    te = get_top_players(lineup, 'TE', 1)[0].points
    best_trio = round(qb + rb + max(wr, te), 2)
    return best_trio

def get_lineup_efficiency(lineup: list):
    max_score = get_best_lineup(lineup)
    real_score = np.sum([player.points for player in lineup if player.slot_position not in ('BE', 'IR')])
    return real_score / max_score
    
def get_weekly_finish(league: League, team: Team, week: int):
    ''' Returns the rank of a team compared to the rest of the league by points for (for the loaded week) '''
    league_scores = [tm.scores[week-1] for tm in league.teams]
    league_scores = sorted(league_scores, reverse=True)
    return league_scores.index(team.scores[week-1]) + 1

def get_num_out(lineup: list):
    ''' Returns the (esimated) number of players who did not play for a team for the loaded week (excluding IR slot players). '''
    num_out = 0
    # TODO: write new code based on if player was injured
    return num_out

def avg_slot_score(lineup: list, slot: str):
    ''' 
    Returns the average score for starting players of a specified slot.
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.mean([player.points for player in lineup if player.slot_position == slot])

def sum_bench_points(lineup: list):
    ''' 
    Returns the total score for bench players
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.sum([player.points for player in lineup if player.slot_position == 'BE'])

def print_weekly_stats(league: League, team: Team, week: int):
    ''' Print the weekly stats for the team during a given week. '''

    lineup = get_lineup(league, team, week)
    stats_table = [['Week Score: ', team.scores[week-1]],
                   ['Best Possible Lineup: ', get_best_lineup(lineup)],
                   ['Opponent Score: ', team.schedule[week-1].scores[week-1]],
                   
                   ['Weekly Finish: ', get_weekly_finish(league, team, week)],
                   ['Best Trio: ', get_best_trio(lineup)],
                   ['Number of Injuries: ', get_num_out(lineup)],
                   ['Starting QB pts: ', avg_slot_score(lineup, 'QB')],
                   ['Avg. Starting RB pts: ', avg_slot_score(lineup, 'RB')],
                   ['Avg. Starting WR pts: ', avg_slot_score(lineup, 'WR')],
                   ['Starting TE pts: ', avg_slot_score(lineup, 'TE')],
                   ['Starting Flex pts: ', avg_slot_score(lineup, 'RB/WR/TE')],
                   ['Starting DST pts: ', avg_slot_score(lineup, r'D/ST')],
                   ['Starting K pts: ', avg_slot_score(lineup, 'K')],
                   ['Total Bench pts: ', sum_bench_points(lineup)]]
    
    print('\n', table(stats_table, headers = ['Week ' + str(week), ''], numalign = 'left'))
    


''' ADVANCED STATS '''
#league.power_rankings(week)

def get_weekly_luck_index(league: League, team: Team, week: int):
    ''' 
    This function returns an index quantifying how 'lucky' a team was in a given week 
    
    Luck index:
        50% probability of playing a team with a lower record
        25% your play compared to previous weeks
        25% opp's play compared to previous weeks
    '''
    opp = team.schedule[week-1]
    num_teams = len(league.teams)
    
    # Luck Index based on where the team and its opponent finished compared to the rest of the league  
    rank = get_weekly_finish(league, team, week)
    opp_rank = get_weekly_finish(league, opp, week)

    if rank < opp_rank:                                # If the team won...
        luck_index = 5 * (rank - 1) / (num_teams - 2)  # Odds of this team playing a team with a higher score than it
    elif rank > opp_rank:                              # If the team lost or tied...
        luck_index = -5 * (num_teams - rank) / (num_teams - 2)    # Odds of this team playing a team with a lower score than it

    # If the team tied...
    elif rank < (num_teams / 2):                                      
        luck_index = -2.5 * (num_teams - rank - 1) / (num_teams - 2)  # They are only half as unlucky, because tying is not as bad as losing
    else:
        luck_index = 2.5 * (rank - 1) / (num_teams - 2)               # They are only half as lucky, because tying is not as good as winning


    # Update luck index based on how team played compared to normal
    team_score = team.scores[week - 1]
    team_avg = np.mean(team.scores[:week])
    team_std = np.std(team.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (team_score - team_avg) / team_std
        
        # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        z_norm = z / (3*team_std) * 2.5
        luck_index += z_norm

    # Update luck index based on how opponent played compared to normal
    opp_score = opp.scores[week - 1]
    opp_avg = np.mean(opp.scores[:week])
    opp_std = np.std(opp.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (opp_score - opp_avg) / opp_std
        
        # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        z_norm = z / (3*opp_std) * 2.5
        luck_index -= z_norm
    
    return luck_index / 10


def get_season_luck_indices(league: League, week: int):
    ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    luck_indices = {team:0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, week)
    return luck_indices




''' GENERAL REPORTING '''

def sort_lineups_by_func(league: League, week: int, func, box_scores=None, **kwargs):
    ''' 
    Sorts league teams according to function. 
    Values are sorted ascending. 
    DOES NOT ACCOUNT FOR TIES
    '''
    if box_scores is None: box_scores = league.box_scores(week)
    return sorted(league.teams, key=lambda x:func(get_lineup(league, x, week, box_scores), **kwargs))

def print_weekly_stats(league: League, week: int):
    ''' Prints weekly stat report for a league during a given week '''
    # Load box scores for specified week
    box_scores = league.box_scores(week)
    
    statsTable = [['Most Points Scored: ', sorted(league.teams, key=lambda x:x.scores[week-1], reverse=True)[0].owner],
                   ['Least Points Scored: ', sorted(league.teams, key=lambda x:x.scores[week-1])[0].owner],
                   ['Best Possible Lineup: ', sort_lineups_by_func(league, week, get_best_lineup, box_scores)[-1].owner],
                   ['Best Trio: ', sort_lineups_by_func(league, week, get_best_trio, box_scores)[-1].owner],
                   ['Worst Trio: ', sort_lineups_by_func(league, week, get_best_trio, box_scores)[0].owner],
                   ['Best Lineup Setter', sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[-1].owner],
                   ['Worst Lineup Setter', sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[0].owner],
                   ['---------------------','----------------'],
                   ['Best QBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='QB')[-1].owner],
                   ['Best RBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='RB')[-1].owner],
                   ['Best WRs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='WR')[-1].owner], 
                   ['Best TEs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='TE')[-1].owner],
                   ['Best Flex: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[-1].owner],
                   ['Best DST: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'D/ST')[-1].owner],
                   ['Best K: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='K')[-1].owner],
                   ['Best Bench:', sort_lineups_by_func(league, week, sum_bench_points, box_scores)[-1].owner],
                   ['---------------------','----------------'],
                   ['Worst QBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='QB')[0].owner],
                   ['Worst RBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='RB')[0].owner],
                   ['Worst WRs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='WR')[0].owner], 
                   ['Worst TEs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='TE')[0].owner],
                   ['Worst Flex: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[0].owner],
                   ['Worst DST: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'D/ST')[0].owner],
                   ['Worst K: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='K')[0].owner],
                   ['Worst Bench:', sort_lineups_by_func(league, week, sum_bench_points, box_scores)[0].owner],
                   ]
    print('\n', table(statsTable, headers = ['Week ' + str(week), ''])) 
    
def print_current_standings(league: League):
    ''' Inputs: None
        Outputs: table (prints current standings)
        This function prints the current standings for a league.
        This function does NOT account for tiebreakers.
    '''        
    standings = league.standings()
    results_table = []
    for team in standings:
        results_table += [[ team.team_name, team.wins, team.losses, team.ties, team.points_for, team.owner ]]
    print('\nWeek {}\n'.format(league.currentMatchupPeriod),  
          table(results_table, 
                headers = ['Team', 'Wins', 'Losses', 'Ties', 'Points Scored', 'Owner'], 
                floatfmt = '.2f'))     