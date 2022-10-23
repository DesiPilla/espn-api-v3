import numpy as np
import pandas as pd

from espn_api.football import League, Team, Player

import requests
from copy import copy
from collections import Counter
from tabulate import tabulate as table


# Get a dictionary of the starting roster slots and number of each for the League (Week 1 must have passed already)
#starting_roster_slots = Counter([p.slot_position for p in league.box_scores(1)[0].home_lineup if p.slot_position not in ['BE', 'IR']])


''' FETCH LEAGUE '''
def set_league_endpoint(league: League):
    if (league.year >= (pd.datetime.today() - pd.DateOffset(months=1)).year):#(dt.datetime.now() - dt.timedelta(540)).year):         # ESPN API v3
        league.endpoint = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(league.year) + "/segments/0/leagues/" + str(league.league_id) + "?"
    else:                           # ESPN API v2
        league.endpoint = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league.league_id) + "?seasonId=" + str(league.year) + '&'
        

def get_roster_settings(league: League):
    ''' This grabs the roster and starting lineup settings for the league
            - Grabs the dictionary containing the number of players of each position a roster contains
            - Creates a dictionary rosterSlots{} that only inlcludes slotIds that have a non-zero number of players on the roster
            - Creates a dictionary startingRosterSlots{} that is a subset of rosterSlots{} and only includes slotIds that are on the starting roster
            - Add rosterSlots{} and startingRosterSlots{} to the League attribute League.rosterSettings
    '''
    print('[BUILDING LEAGUE] Gathering roster settings information...')
    
    # This dictionary maps each slotId to the position it represents
    rosterMap = { 0 : 'QB', 1 : 'TQB', 2 : 'RB', 3 : 'RB/WR', 4 : 'WR',
                       5 : 'WR/TE', 6 : 'TE', 7 : 'OP', 8 : 'DT', 9 : 'DE',
                       10 : 'LB', 11 : 'DL', 12 : 'CB', 13 : 'S', 14 : 'DB',
                       15 : 'DP', 16 : 'D/ST', 17 : 'K', 18 : 'P', 19 : 'HC',
                       20 : 'BE', 21 : 'IR', 22 : '', 23 : 'RB/WR/TE', 24 : ' '
                       }
        
    endpoint = '{}view=mMatchupScore&view=mTeam&view=mSettings'.format(league.endpoint)    
    r = requests.get(endpoint, cookies=league.cookies).json()
    if type(r) == list:
        r = r[0]
    settings = r['settings']
    league.name = settings['name']

    roster = settings['rosterSettings']['lineupSlotCounts']    # Grab the dictionary containing the number of players of each position a roster contains
    rosterSlots = {}                                                # Create an empty dictionary that will replace roster{}
    startingRosterSlots = {}                                        # Create an empty dictionary that will be a subset of rosterSlots{} containing only starting players
    for positionId in roster:
        position = rosterMap[int(positionId)]
        if roster[positionId] != 0:                                 # Only inlclude slotIds that have a non-zero number of players on the roster
            rosterSlots[position] = roster[positionId]
            if positionId not in ['20', '21', '24']:              # Include all slotIds in the startingRosterSlots{} unless they are bench, injured reserve, or ' '
                startingRosterSlots[position] = roster[positionId]
    league.roster_settings = {'roster_slots' : rosterSlots, 'starting_roster_slots' : startingRosterSlots}    # Add rosterSlots{} and startingRosterSlots{} as a league attribute
    return


def fetch_league(league_id: int, year: int, swid: str, espn_s2: str):
    print('[BUILDING LEAGUE] Fetching league data...')
    league = League(league_id=league_id,
                    year=year,
                    swid=swid, 
                    espn_s2=espn_s2)  
    
    # Set cookies
    league.cookies = {'swid':swid, 'espn_s2':espn_s2}
    
    # Set league endpoint
    set_league_endpoint(league)
    
    # Get roster information
    get_roster_settings(league)
    
    # Load current league data
    print('[BUILDING LEAGUE] Loading current league details...')
    league.load_roster_week(league.current_week)
    return league



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


def get_best_lineup(league: League, lineup: list):
    ''' Returns the best possible lineup for team during the loaded week. '''
    # Save full roster
    saved_roster = copy(lineup)
    
    # Find Best Lineup
    best_lineup = []
    for slot in sorted(league.roster_settings['starting_roster_slots'].keys(), key=len):  # Get best RB before best RB/WR/TE
        num_players = league.roster_settings['starting_roster_slots'][slot]
        best_players = get_top_players(saved_roster, slot, num_players)
        best_lineup.extend(best_players)
        
        # Remove selected players from consideration for other slots
        for player in best_players:
            saved_roster.remove(player)

    return np.sum([player.points for player in best_lineup])


def get_best_trio(league: League, lineup: list):
    ''' Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week. '''
    qb = get_top_players(lineup, 'QB', 1)[0].points
    rb = get_top_players(lineup, 'RB', 1)[0].points
    wr = get_top_players(lineup, 'WR', 1)[0].points
    te = get_top_players(lineup, 'TE', 1)[0].points
    best_trio = round(qb + rb + max(wr, te), 2)
    return best_trio

def get_lineup_efficiency(league: League, lineup: list):
    max_score = get_best_lineup(league, lineup)
    real_score = np.sum([player.points for player in lineup if player.slot_position not in ('BE', 'IR')])
    return real_score / max_score
    
def get_weekly_finish(league: League, team: Team, week: int):
    ''' Returns the rank of a team compared to the rest of the league by points for (for the loaded week) '''
    league_scores = [tm.scores[week-1] for tm in league.teams]
    league_scores = sorted(league_scores, reverse=True)
    return league_scores.index(team.scores[week-1]) + 1

def get_num_out(league: League, lineup: list):
    ''' Returns the (esimated) number of players who did not play for a team for the loaded week (excluding IR slot players). '''
    num_out = 0
    # TODO: write new code based on if player was injured
    return num_out

def avg_slot_score(league: League, lineup: list, slot: str):
    ''' 
    Returns the average score for starting players of a specified slot.
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.mean([player.points for player in lineup if player.slot_position == slot])

def sum_bench_points(league: League, lineup: list):
    ''' 
    Returns the total score for bench players
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.sum([player.points for player in lineup if player.slot_position == 'BE'])



''' ADVANCED STATS '''
#league.power_rankings(week)

def get_weekly_luck_index(league: League, team: Team, week: int, verbose=False):
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
        team_z = (team_score - team_avg) / team_std
        
        # Noramlize the z-score so that a performance 1 std dev's away from the mean has an effect of 1 points on the luck index
        team_z_norm = team_z
        luck_index += team_z_norm

    # Update luck index based on how opponent played compared to normal
    opp_score = opp.scores[week - 1]
    opp_avg = np.mean(opp.scores[:week])
    opp_std = np.std(opp.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        opp_z = (opp_score - opp_avg) / opp_std
        
        # Noramlize the z-score so that a performance 1 std dev away from the mean has an effect of 1 points on the luck index
        opp_z_norm = opp_z
        luck_index -= opp_z_norm
    
    if verbose:
        print("Team: {}".format(team))
        print("Team rank: {}".format(rank))
        print("Team score: {}".format(team_score))
        print("Team avg: {:.2f}".format(team_avg))
        print("Team std: {:.2f}".format(team_std))
        print("Team z: {}".format(team_z))
        print("Team z_norm: {}".format(team_z_norm))
        print()
        print("Opponent: {}".format(opp))
        print("Opponent rank: {}".format(opp_rank))
        print("Opponent score: {}".format(opp_score))
        print("Opponent avg: {:.2f}".format(opp_avg))
        print("Opponent std: {:.2f}".format(opp_std))
        print("Opponent z: {}".format(opp_z))
        print("Opponent z_norm: {}".format(opp_z_norm))
    return luck_index * 10

def get_season_luck_indices(league: League, week: int):
    ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    luck_indices = {team:0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, wk)
    return luck_indices


def get_season_luck_indices(league: League, week: int):
    ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    luck_indices = {team:0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, wk)
    return luck_indices


def sort_lineups_by_func(league: League, week: int, func, box_scores=None, **kwargs):
    ''' 
    Sorts league teams according to function. 
    Values are sorted ascending. 
    DOES NOT ACCOUNT FOR TIES
    '''
    if box_scores is None: box_scores = league.box_scores(week)
    return sorted(league.teams, key=lambda x:func(league, get_lineup(league, x, week, box_scores), **kwargs))
    
    


''' HISTORICAL DRAFT ANALYTICS '''
def get_draft_details(league: League):
    draft = pd.DataFrame()
    
    # Get a dictionary of the starting roster slots and number of each for the League (Week 1 must have passed already)
    primary_slots = [slot for slot in league.roster_settings['starting_roster_slots'].keys() if ('/' not in slot) or (slot == 'D/ST')]

    for i, player in enumerate(league.draft):
        draft.loc[i, 'year'] = league.year
        draft.loc[i, 'team_owner'] = player.team.owner
        draft.loc[i, 'team_id'] = player.team.team_id
        draft.loc[i, 'player_name'] = player.playerName
        draft.loc[i, 'player_id'] = player.playerId
        draft.loc[i, 'round_num'] = player.round_num
        draft.loc[i, 'round_pick'] = player.round_pick
        try:
            # Get more player details (can take 1.5 min)
            player = league.player_info(playerId=draft.loc[i, 'player_id'])
            draft.loc[i, 'pro_team'] = player.proTeam
            draft.loc[i, 'proj_points'] = player.projected_total_points
            draft.loc[i, 'total_points'] = player.total_points
            draft.loc[i, 'position'] = [slot for slot in player.eligibleSlots if slot in primary_slots][0]
        except AttributeError:
            print('Pick {} missing.'.format(i+1))
            draft.loc[i, 'player_name'] = ''
            draft.loc[i, 'player_id'] = ''
            draft.loc[i, 'round_num'] = 99
            draft.loc[i, 'round_pick'] = 99
        except:
            print(i, player, league.draft[i-2:i+2])
            draft.loc[i, 'position'] = player.eligibleSlots[0]

    draft['first_letter'] = draft.player_name.str[0]
    draft['points_surprise'] = draft.total_points - draft.proj_points
    draft['positive_surprise'] = draft.points_surprise > 0
    draft['pick_num'] = (draft.round_num - 1) * len(draft.team_id.unique()) + draft.round_pick
            
    draft_pick_values = pd.read_csv('./pick_value.csv')
    draft = pd.merge(draft, draft_pick_values, left_on='pick_num', right_on='pick', how='left').drop(columns=['pick'])
    return draft

def get_multiple_drafts(league: League, start_year: int = 2020, end_year: int = 2021, swid=None, espn_s2=None):
    draft = pd.DataFrame()
    for year in range(start_year, end_year+1):
        print('Fetching {} draft...'.format(year), end='')
        try:
            draft_league = League(league_id=league.league_id,
                                  year=year,
                                  swid=swid, 
                                  espn_s2=espn_s2)
        except: continue
        
        draft = pd.concat([draft, get_draft_details(draft_league)])
    
    return draft


def get_team_max(df, col, by='team_owner', keep=None):
    '''
    `by` = 'team_id', 'team_owner'
    '''
    
    def get_maxs(s):
        return ' | '.join(s[s == s.max()].index.values)

    value_counts = df.groupby([by, col])\
                     .count()['player_id']\
                     .unstack()\
                     .fillna(0)

    value_counts['max_value'] = value_counts.apply(get_maxs, axis=1)
    value_counts['max_count'] = value_counts.max(axis=1)
    value_counts = value_counts.iloc[:, -2:]
    
    if keep is not None:
        return value_counts[value_counts.index.isin(keep)]
    
    else: return value_counts





''' DJANGO WEB FUNCTIONS '''
def django_weekly_stats(league: League, week: int):
    # Load box scores for specified week
    box_scores = league.box_scores(week)
    
    best_table =  [
        ['Most Points Scored: ', sorted(league.teams, key=lambda x:x.scores[week-1], reverse=True)[0].owner],
        ['Best Possible Lineup: ', sort_lineups_by_func(league, week, get_best_lineup, box_scores)[-1].owner],
        ['Best Trio: ', sort_lineups_by_func(league, week, get_best_trio, box_scores)[-1].owner],
        ['Best Lineup Setter', sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[-1].owner],
        ['Best QBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='QB')[-1].owner],
        ['Best RBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='RB')[-1].owner],
        ['Best WRs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='WR')[-1].owner], 
        ['Best TEs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='TE')[-1].owner],
        ['Best Flex: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[-1].owner],
        ['Best DST: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'D/ST')[-1].owner],
        ['Best K: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='K')[-1].owner],
        ['Best Bench:', sort_lineups_by_func(league, week, sum_bench_points, box_scores)[-1].owner]
    ]
    worst_table = [
        ['Least Points Scored: ', sorted(league.teams, key=lambda x:x.scores[week-1])[0].owner],
        ['---------------------','----------------'],
        ['Worst Trio: ', sort_lineups_by_func(league, week, get_best_trio, box_scores)[0].owner],
        ['Worst Lineup Setter', sort_lineups_by_func(league, week, get_lineup_efficiency, box_scores)[0].owner],
        ['Worst QBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='QB')[0].owner],
        ['Worst RBs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='RB')[0].owner],
        ['Worst WRs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='WR')[0].owner], 
        ['Worst TEs: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='TE')[0].owner],
        ['Worst Flex: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'RB/WR/TE')[0].owner],
        ['Worst DST: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot=r'D/ST')[0].owner],
        ['Worst K: ', sort_lineups_by_func(league, week, avg_slot_score, box_scores, slot='K')[0].owner],
        ['Worst Bench:', sort_lineups_by_func(league, week, sum_bench_points, box_scores)[0].owner],
    ]

    weekly_stats = []
    for i in range(len(best_table)):
        weekly_stats.append({
            'best_label':best_table[i][0],
            'best_owner':best_table[i][1],
            'worst_label':worst_table[i][0],
            'worst_owner':worst_table[i][1]
        })

    return weekly_stats


def django_power_rankings(league: League, week: int):
    '''
    To get the current week stats, pass in current_week - 1 into the function.
    '''
    # Get power rankings for the current week
    league_power_rankings = league.power_rankings(week)
    
    # Add the power rankings for each team
    power_rankings = []
    for i in range(len(league_power_rankings)):
        power_rankings.append({
            'team':league_power_rankings[i][1].team_name,
            'value':league_power_rankings[i][0],
            'owner':league_power_rankings[i][1].owner
        })

    return power_rankings

def django_luck_index(league: League, week: int):
    # Get luck index for the current week
    league_luck_index = get_season_luck_indices(league, week)
    
    # Add the luck index for each team
    luck_index = []
    for (team, luck) in sorted(league_luck_index.items(), key=lambda x:x[1], reverse=True):
        luck_index.append({
            'team':team.team_name,
            'value':'{:.1f}'.format(luck),
            'owner':team.owner
        })

    return luck_index

def django_standings(league: League):
    # Get power rankings for the current week
    league_standings = league.standings()
    
    # Add the power rankings for each team
    standings = []
    for team in league_standings:
        standings.append({
            'team':team.team_name,
            'wins':team.wins,
            'losses':team.losses,
            'ties':team.ties,
            'points_for':'{:.1f}'.format(team.points_for),
            'owner':team.owner,
        })

    return standings