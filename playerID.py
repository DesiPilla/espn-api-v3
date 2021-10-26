from league import League
from authorize import Authorize
from team import Team
from player import Player
from utils.building_utils import getUrl
from itertools import chain

import pandas as pd
import numpy as np
import requests
import math
from tabulate import tabulate as table
import os
import sys
from fpdf import FPDF
import argparse
import progressbar
import re
import scrape_values


user_id = 'desi'
year = 2021

# Get login credentials for leagues
# login = pd.read_csv('C:\\Users\\desid\\Documents\\Fantasy_Football\\espn-api-v3\\login.csv')
# _, username, password, league_id, swid, espn_s2 = login[login['id'] == user_id].values[0]
username = 'cgeer98'
password = 'Penguins1'
league_id = 916709
swid = '{75C7094F-C467-4145-8709-4FC467C1457E}'
espn_s2 = 'AECbQaX7HoUGyJ5X5cmNlFHVs%2FmDl0RKfnVV%2FazefK9PxoSfENQFF6ULNnR421xium4UYV5dC0GsOhS%2BeigBuhk1abpSjhlXDCJnIGt0PjUHCZpV6qF5S9qMS40ichi2XnVZFSKwAid6h8bFbWA4eHclC%2BJHqMyirQ85yLRG6zc6nULRaovpF2Cx2j5U55OuvwTnI2HCztRnEJIVucnKxlem7pAidup27BIggM3c42%2BrH7vXUlRaIYXhjE%2BGH3cWbL88H8AcpIQpG%2Bft96vAZXuB'
root = '/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3'


# Generate cookies payload and API endpoint
cookies = {'swid' : swid, 'espn_s2' : espn_s2}
url = getUrl(year, league_id)


league = League(league_id, year, username, password, swid, espn_s2)
# print(league, "\n")

# create list of team objects
teams = league.teams
teams = list(teams.values())

# week = 1

#### TODO: Find a way to cleanly merge espn IDs with Dynasty Process ID chart

def get_player_values(week):
    # create list of player objects from list of team objects
    players = []
    rosters = []

    for team in teams:
        rosters = team.rosters

        thisWkRosters = rosters.get(week)

        for player in thisWkRosters:
            playerID = [team.teamName, player.name, player.positionId, player.id]
            players.append(playerID)

        # print(players)

    # values = pd.read_csv("/users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/playerValues.csv")
    # values = values[['player','pos', 'age', 'value_1qb', 'fp_id']]
    values = scrape_values.player_values(week)

    values = pd.DataFrame(values)

    # values_file = '/users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/values/week' + str(week) + '.csv'

    # values = pd.read_csv(values_file)


    # print(values)
    values.columns = values.columns.str.lower()

    # fix player names to match between dataframes
    values['player'] = values['player'].replace('Darrell Henderson', 'Darrell Henderson Jr.', regex=True)
    values['player'] = values['player'].replace('Melvin Gordon', 'Melvin Gordon III', regex=True)
    values['player'] = values['player'].replace('JK Dobbins', 'J.K. Dobbins', regex=True)
    values['player'] = values['player'].replace('Michael Pittman', 'Michael Pittman Jr.', regex=True)
    values['player'] = values['player'].replace('D.J. Chark', 'DJ Chark Jr.', regex=True)
    values['player'] = values['player'].replace('Marvin Jones', 'Marvin Jones Jr.', regex=True)
    values['player'] = values['player'].replace('Odell Beckham', 'Odell Beckham Jr.', regex=True)
    values['player'] = values['player'].replace('Allen Robinson', 'Allen Robinson II', regex=True)
    values['player'] = values['player'].replace('D.J. Moore', 'DJ Moore', regex=True)

    # values['player'] = values['player'].replace('D.J. Chark', 'DJ Chark Jr.', regex=True)
    # values['player'] = values['player'].replace('Allen Robinson', 'Allen Robinson II', regex=True)
    # values['player'] = values['player'].replace('D.J. Moore', 'DJ Moore', regex=True)
    # values['player'] = values['player'].replace('Michael Pittman', 'Michael Pittman Jr.', regex=True)
    # values['player'] = values['player'].replace('Odell Beckham', 'Odell Beckham Jr.', regex=True)
    # values['player'] = values['player'].replace('Laviska Shenault', 'Laviska Shenault Jr.', regex=True)
    # values['player'] = values['player'].replace('Darrell Henderson', 'Darrell Henderson Jr.', regex=True)
    #
    # missingPlayer = ['William Fuller V','7.00','-0.8']
    # missingPlayer2 = ['Chuba Hubbard','6.61','+1.5']
    # missingPlayer3 = ['Damien Williams','8.1','-2.6']
    # missingPlayer4 = ['Devontae Booker','6.34','+1.3']
    # missingPlayer5 = ['Khalil Herbert','3.47','+3.3']
    # missingPlayer6 = ['Taylor Heinicke','5.58','-1.3']
    #
    #
    # missing = pd.DataFrame([missingPlayer],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer2],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer3],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer4],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer5],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer6],columns=['player','rating','change'])
    # values = values.append(missing, ignore_index=True)

    # values['player'] = values['player'].replace(r' \(.*\)', '', regex=True)
    # values['player'] = re.sub(r"\([^()]*\)", "", values['player'])

    # Get starters only
    players = pd.DataFrame(players, columns = ['team', 'player', 'posID', 'espn_id'])
    players = players[players['posID'] != 17] # remove kickers
    players = players[players['espn_id'] > 0] # remove D/ST
    # players = players[(players['posID'] < 17) | (players['posID'] == 23)] # starters and flex ONLY
    players = players.drop(['posID','espn_id'], axis=1)
    # print("PLAYERS :", players)

    # players['player'] = players['player'].astype(str)
    # values['player'] = values['player'].astype(str)

    # print(players.dtypes)
    # print(values.dtypes)

    # players.set_index('player')
    # values.set_index('player')

    joined = players.merge(values, on='player', how='left')
    joined['rating'] = joined['rating'].map(float)

    grouped = joined.groupby(['team', 'position'])

    # for key, item in grouped:
    #     print(grouped.get_group(key), "\n\n")

    joined['pos_rank'] = joined.groupby(['team', 'position'])['rating'].rank(method='first',ascending=False)

    flexConditions = [
    (joined['position'] == 'RB') & (joined['pos_rank'] > 2),
    (joined['position'] == 'WR') & (joined['pos_rank'] > 3),
    (joined['position'] == 'TE') & (joined['pos_rank'] > 1),
    ]

    flex = [1, 1, 1]

    joined['flex'] = np.select(flexConditions, flex)

    joined['flexRank'] = joined.groupby(['team','flex'])['rating'].rank(method='first',ascending=False)

    starters = joined[(joined['position'] == 'QB') & (joined['pos_rank'] ==  1) | (joined['position'] == 'RB') & (joined['pos_rank'] <= 2) | (joined['position'] == 'WR') & (joined['pos_rank'] <= 3) | (joined['position'] == 'TE') & (joined['pos_rank'] == 1) | (joined['flex'] == 1) & (joined['flexRank'] == 1)]
    # print(table(starters, headers='keys'))


    starters.to_csv(root + '/values/week' + str(week) + '.csv')


    return(starters)

# def get_player_values_lw(week):
    # create list of player objects from list of team objects
    players = []
    rosters = []

    for team in teams:
        rosters = team.rosters

        thisWkRosters = rosters.get(week)

        for player in thisWkRosters:
            playerID = [team.teamName, player.name, player.positionId, player.id]
            players.append(playerID)

            # print(players)

    values = pd.read_csv("/users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/playerValues",week,".csv")
    values = values[['player','pos', 'age', 'value_1qb', 'fp_id']]

    values.columns = values.columns.str.lower()
    # print(values)


    # Remove team from FFanalytics_week2
    # values['player'] = values['player'].replace(r' \(.*\)', '', regex=True)


    players = pd.DataFrame(players, columns = ['team', 'player', 'posID', 'espn_id'])
    players = players[players['posID'] != 17]
    players = players[players['espn_id'] > 0]
    players = players[(players['posID'] < 17) | (players['posID'] == 23)]

    # print("PLAYERS :", players)

    players['player'] = players['player'].map(str)
    values['player'] = values['player'].map(str)

    # print(players.dtypes)
    # print(values.dtypes)

    players.set_index('player')
    values.set_index('player')

    joined = players.merge(values, how='left')

    return(joined)
