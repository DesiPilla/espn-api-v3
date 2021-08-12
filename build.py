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