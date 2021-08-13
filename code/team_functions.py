import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from espn_api.football import League, Team, Player

from collections import Counter



def get_top_players(team: Team, slot: str, n: int):
    ''' Takes a list of players and returns a list of the top n players based on points scored. '''
    # Gather players of the desired position
    eligible_players = []
    for player in team.roster:
        if slot in player.eligibleSlots:
            eligible_players.append(player)
            
    return sorted(eligible_players, key=lambda x: x.stats[1]['points'], reverse=True)[:n]


def get_best_lineup(team: Team):
    ''' Returns the best possible lineup for team during the loaded week. '''
    # Save full roster 
    saved_roster = team.roster[:]

    # Find Best Lineup
    best_lineup = []
    for slot in sorted(starting_roster_slots.keys(), key=len):  # Get best RB before best RB/WR/TE
        num_players = starting_roster_slots[slot]
        best_players = get_top_players(team, slot, num_players)
        best_lineup.extend(best_players)
        
        # Remove selected players from consideration for other slots
        for player in best_players:
            team.roster.remove(player)
            
    # Restore original roster
    team.roster = saved_roster

    return np.sum([player.stats[1]['points'] for player in best_lineup])


def get_best_trio(team: Team):
    ''' Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week. '''
    qb = get_top_players(team, 'QB', 1)[0].stats[1]['points']
    rb = get_top_players(team, 'RB', 1)[0].stats[1]['points']
    wr = get_top_players(team, 'WR', 1)[0].stats[1]['points']
    te = get_top_players(team, 'TE', 1)[0].stats[1]['points']
    best_trio = round(qb + rb + max(wr, te), 2)
    return best_trio

def get_weekly_finish(team: Team):
    ''' Returns the rank of a team compared to the rest of the league by points for (for the loaded week) '''
    league_scores = sorted(league.teams, key=lambda x: x.scores[week], reverse=True)
    return league_scores.index(team) + 1

def get_num_out(team: Team):
    ''' Returns the (esimated) number of players who did not play for a team for the loaded week (excluding IR slot players). '''
    num_out = 0
    # TODO: write new code based on if player was injured
    return num_out

def avg_starting_score_slot(lineup: list, slot: str):
    ''' 
    Returns the average score for starting players of a specified slot.
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.mean([player.stats[1]['points'] for player in box_score.home_lineup if player.slot_position == slot])

def total_bench_points(lineup: list):
    ''' 
    Returns the total score for bench players
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.sum([player.stats[1]['points'] for player in box_score.home_lineup if player.slot_position == 'BE'])







''' ADVANCED STATS '''

def get_weekly_luck_index(league: League, team: Team, week: int, num_teams: int):
    ''' 
    This function returns an index quantifying how 'lucky' a team was in a given week 
    
    Luck index:
        50% probability of playing a team with a lower record
        25% your play compared to previous weeks
        25% opp's play compared to previous weeks
    '''
    opp = team.schedule[week-1]
    
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
            luck_indices[team] += get_weekly_luck_index(team, week, len(league.teams))
    return luck_indices