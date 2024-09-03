'''
TODO:
1. Fix expected standings
2. Clean up code (value rankings)
3. Luck Index
4. LLM Weekly reviews
'''

import playerID
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
import argparse
import progressbar
from espn_api.football import League
from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the NFL season to run rankings for')
args = parser.parse_args()
week = int(args.week)

# Define user and season year
user_id = 'cgeer98'
year = datetime.now().year

# Get login credentials for leagues
# login = pd.read_csv('C:\\Users\\desid\\Documents\\Fantasy_Football\\espn-api-v3\\login.csv')
# _, username, password, league_id, swid, espn_s2 = login[login['id'] == user_id].values[0]
username = 'cgeer98'
password = 'Penguins1!'
league_id = 916709
swid = '{75C7094F-C467-4145-8709-4FC467C1457E}'
espn_s2 = 'AEAldgr2G2n0JKOnYGii6ap3v4Yu03NjpuI2D0SSZDAMoUNm0y2DKP4GRofzL8sn%2Bzoc%2FAVwYxZ9Z9YvhFXPxZq9VE1d5KZIFOPQUWvx9mhdI0GJQUQU3OMid9SySbpzCI7K5hQ3LoxVAjqNT%2FvaIRy%2F7G8qm4l%2BL8fPBouCQI7k9W7c01T3J4RqFoQ3g%2B3ttyHKqhvg7DWDUkXNzJyxgFytKiRqah%2Fb77L67CD0bS7SFzFZPt%2BOrTohER9w8Lxoi0W0dAA%2BmqCfXzUTh9%2FEdxcf'

root = '/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/'

league = League(league_id, year, espn_s2, swid)
print(league, "\n")

# Create list of team objects
teams = league.teams

# Extract team names using list comprehension
team_names = [team.team_name for team in teams]

if week > 1:

    # create table for last week to compare for weekly change
    lw_allplay = lw_allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False)
    lw_allplay['PowerScore'] = lw_allplay['PowerScore'].round(2)
    lw_allplay = lw_allplay.reset_index()

    # create empty lists to add to in the for loop (Value Informed Ranking)
    diffs = []
    emojis = []
    emoji_names = teams.copy()

    tw_rankings = allplay_ps
    lw_rankings = pd.read_csv(root + 'past_rankings/week' + str(week-1) + '.csv')

    print('This week: \n', tw_rankings)
    print('Last week: \n', lw_rankings)

    for team in teams:
        tw_index = tw_rankings[tw_rankings['team'] == team].index.values # get index values of this weeks power rankigns
        lw_index = lw_rankings[lw_rankings['team'] == team].index.values  # get index values of last weeks power rankings
        diff = lw_index-tw_index # find the difference between last week to this week
        diff = int(diff.item()) # turn into list to iterate over
        diffs.append(diff) # append to the list

    # iterate over diffs list and edit values to include up/down arrow emoji and the number of spots the team moved
    for item in diffs:
        if item > 0:
            emojis.append("**<span style=\"color: green;\">⬆️ " + str(abs(item)) + " </span>**" )
        elif item < 0:
            emojis.append("**<span style=\"color: red;\">⬇️ " + str(abs(item)) + " </span>**")
        elif item == 0:
            emojis.append("") # adds a index of nothing for teams that didn't move

    Value_Power_Rankings_print.insert(loc=1, column='Weekly Change', value=emojis) # insert the weekly change column

# Set index for printing tables to start at 1
allplay.index = np.arange(1, len(allplay) + 1)
allplay_ps.index = np.arange(1, len(allplay_ps) + 1)
if week >5:
    projections.index = np.arange(1, len(projections) + 1)
team_scores_prt.index = np.arange(1, len(team_scores_prt) + 1)
# projectedStandings_prnt.index = np.arange(1, len(projectedStandings_prnt) + 1)
# Value_Power_Rankings_print.index = np.arange(1, len(Value_Power_Rankings) + 1)


# Print everything
# open text file
filepath = "/Users/christiangeer/Fantasy_Sports/football/power_rankings/jtown-dynasty/content/blog/Week"+ str(week) + str(year) + "PowerRankings.md"
sys.stdout = open(filepath, "w")

# for the markdown files in blog
print("---")
print("title: Week " + str(week) + " ", datetime.now().year, " Report")
print("date: 2020-", datetime.now().month,"-",datetime.now().day)
print("image: /images/",datetime.now().year, "week" + str(week) + ".jpeg")
print("draft: true")
print("---")

print("<!-- excerpt -->")

print("\n# POWER RANKINGS\n")
# Value un-informed
print(table(allplay_ps, headers='keys', tablefmt='pipe', numalign='center')) # have to manually center all play % because its not a number

# Value Informed
# print(table(Value_Power_Rankings_print, headers='keys',tablefmt='pipe', numalign='center')) # have to manually center all play % and weekly change because not an int

print('\n##Highlights:\n')

# print("\n# EXPECTED STANDINGS (as of week ", week, ")")
# league.printExpectedStandings(week)
# print(table(projectedStandings_prnt, headers='keys', tablefmt='pipe', numalign='center'))

# if week >= 5:
#     print("\n# PLAYOFF PROBABILITIES (as of week ", week, ")")
#     print(table(projections, headers='keys', tablefmt='pipe', numalign='center'))


# print("\n# LUCK INDEX")
# league.printLuckIndex(week)

# print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))

# close text file
sys.stdout.close()
