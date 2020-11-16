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

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the season')
args = parser.parse_args()
week = int(args.week)



# Define user and season year
user_id = 'desi'
year = 2020

# Get login credentials for leagues
# login = pd.read_csv('C:\\Users\\desid\\Documents\\Fantasy_Football\\espn-api-v3\\login.csv')
# _, username, password, league_id, swid, espn_s2 = login[login['id'] == user_id].values[0]
username = 'cgeer98'
password = 'Penguins1'
league_id = 916709
swid = '{75C7094F-C467-4145-8709-4FC467C1457E}'
espn_s2 = 'AEAVW%2B1kBbZavpoBSNScdoswT0j4x1tctoQm4hzikgixD4YmSRMxlsEdnREHR4%2F4FcLfrxfmrRi06ARQNc9WU%2FKEdSjfB5inJeGqIW4E%2BO98dbPDADbaAWIoYaIGp074d4jr7Glf%2Fm1TkBEYhpAa%2F5gAnyrj7GEfPPy7O20%2FWQnenImjXccRFKN%2Bi23D19zshjZRZkENyN5txKmi8%2BdKr%2BTY4tiJEG5PHeAysqougAPJPexDYu2Lj3XSmzc4pkBVXHM0058gmcylXnxmraYxp34K3tMkXxjXIs0sEJ9nuI4nIw%3D%3D'



# Generate cookies payload and API endpoint
cookies = {'swid' : swid, 'espn_s2' : espn_s2}
url = getUrl(year, league_id)


league = League(league_id, year, username, password, swid, espn_s2)
print(league)

dynastyProcessValues = pd.read_csv("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/data/files/values-players.csv")
dynastyProcessValues = dynastyProcessValues[["player","value_1qb"]]


# create for loop to add team names from team objects into list
teams = league.teams
teams_list = list(teams.values())
team_names = []
for team in teams_list:
    team_name = team.teamName
    team_names.append(team_name)

seasonScores = []

for team in teams_list:
    weeklyScores = team.scores
    seasonScores.append(weeklyScores)

seasonScores_df = pd.DataFrame(data=seasonScores)
teams_names_df = pd.DataFrame(data=team_names,columns=['Team'])
team_scores = teams_names_df.join(seasonScores_df)

# get df headings for subsetting df
team_scores_headings = list(team_scores)

# get headings for up to selected week
current_week_headings = team_scores_headings[1:week+1]

# set the index to the team column
team_scores = team_scores.set_index('Team')
scores = team_scores.copy()

# create a row for the league average for each week
team_scores.loc['League Average'] = (team_scores.sum(numeric_only=True, axis=0)/8).round(2)

# subract each teams score from the league average for that week
team_scores[:] = team_scores[:] - team_scores.loc['League Average']
team_scores = team_scores.drop("League Average") # leageue average no longer necessary
team_scores_log = team_scores.copy()

logged_ps = team_names.copy()
logged_ps = pd.DataFrame(logged_ps, columns=['team'])
logged_ps['lnPowerScore'] = 0
logged_ps = logged_ps.set_index('team')

column = []
tables = []
tables_names = team_names.copy()
tables_names = pd.DataFrame(tables_names, columns=["team"])


team_scores_log_col = list(team_scores_log[1:])
compute_week = 1


for col in current_week_headings:
    for row in team_scores_log[col]:
        if col == 1:
            lnRow = row * 1
        else:
            lnRow = row * (math.log(col))
        column.append(round(lnRow, 2))
    tables.append(column)
    column = []

tables_df = pd.DataFrame(tables)


tables_df = tables_df.T

tables_df['PowerScore'] = tables_df.sum(numeric_only=True, axis=1)
tables_df = tables_df.reset_index(drop=True)

logWeightedPS = tables_names.join(tables_df)
logWeightedPS = logWeightedPS.sort_values(by="PowerScore", ascending=False)
logWeightedPS = logWeightedPS.reset_index(drop=True)
logWeightedPS_prnt = logWeightedPS[['team', 'PowerScore']]


# team_scores_pr = team_names.copy()
# team_scores_pr = pd.DataFrame(team_scores_pr,columns=['team'])
# team_scores_pr['Power Score'] = 0
# team_scores_pr = team_scores_pr.set_index('team')
#
# team_scores_pr_head = list(team_scores_pr)
# print(team_scores_pr)
# print(team_scores_pr_head)

# calculate with for loop
# while compare_week <= week:
#     for row in scores.itertuples():
#         team_scores_pr.loc[row[0],team_scores_pr[0]] += (math.log(row))
#
#     compare_week += 1



# get columns for calculating power score
last = current_week_headings[-1]
if len(current_week_headings) > 1:
    _2last = current_week_headings[-2]

if len(current_week_headings) > 2:
    _3last = current_week_headings[-3]

if len(current_week_headings) > 3:
    rest = current_week_headings[0:-3]


if len(current_week_headings) == 1:
    team_scores['Power_Score'] = (team_scores[last])
elif len(current_week_headings) == 2:
    team_scores['Power_Score'] = ((team_scores[last]*.6) + (team_scores[_2last])*.4)/1
elif len(current_week_headings) == 3:
    team_scores['Power_Score'] = ((team_scores[last]*.25) + (team_scores[_2last]*.15) + (team_scores[_3last]*.1))/.5
else:
    team_scores['Power_Score'] = ((team_scores[last]*.3) + (team_scores[_2last]*.15) + (team_scores[_3last]*.1) + (team_scores[rest].mean(axis=1)*.45))/1

team_scores = team_scores.sort_values(by='Power_Score', ascending=False)

last_3 = current_week_headings[-3:]
team_scores['3_wk_roll_avg'] = (team_scores[last_3].sum(axis=1)/3).round(2)

# creating season average column
season = list(team_scores)
season = season[1:-1]
team_scores['Season_avg'] = (team_scores[season].sum(axis=1)/week).round(2)

team_scores_prt = team_scores['Power_Score'].round(2)
team_scores_prt = team_scores_prt.reset_index()
# team_scores_prt = team_scores.columns['team','Power Score']

# All play power RANKINGS
allplay = team_names.copy()
allplay = pd.DataFrame(allplay,columns=['team'])
allplay['allPlayWins'] = 0
allplay['allPlayLosses'] = 0
allplay['PowerScore'] = 0
allplay = allplay.set_index('team')

allplay_head = list(allplay)

compare_week = current_week_headings[0]

# compare with for loop
while compare_week <= week:
    for first_row in scores.itertuples():
        for second_row in scores.itertuples():
            if first_row[compare_week] > second_row[compare_week]:
                allplay.loc[first_row[0],allplay_head[0]] += 1
                allplay.loc[first_row[0],allplay_head[2]] += (1 + (math.log(compare_week)))
            if first_row[compare_week] < second_row[compare_week]:
                allplay.loc[first_row[0],allplay_head[1]] += 1
            else:
                continue
    compare_week += 1


allplay = allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False)
allplay['PowerScore'] = allplay['PowerScore'].round(2)
allplay = allplay.reset_index()

# create allplay table sorted by power score
allplay_ps = allplay.sort_values(by='PowerScore', ascending=False)
allplay_ps = allplay_ps.reset_index(drop=True)

# Set index for printing tables to start at 1
allplay.index = np.arange(1, len(allplay) + 1)
allplay_ps.index = np.arange(1, len(allplay_ps) + 1)
team_scores_prt.index = np.arange(1, len(team_scores_prt) + 1)
logWeightedPS_prnt.index = np.arange(1, len(logWeightedPS_prnt) + 1)


# Print everything
# open text file
filepath = "/Users/christiangeer/Fantasy_Sports/Fantasy_FF/power_rankings/jtown-dynasty/content/blog/Week"+ str(week) + "PowerRankings.md"
sys.stdout = open(filepath, "w")

print("---")
print("title: ")
print("date: 2020-10-14T16:34:00.000Z")
print("image: /images/week(ADD WEEK NUMBER HERE).jpg")
print("draft: false")
print("---")

print("\n### EXPECTED STANDINGS (as of week ", week, ")")
league.printExpectedStandings(week)

print("<!-- excerpt -->")

print("\n### POWER RANKINGS\n")
print(table(allplay_ps, headers='keys', tablefmt='github'))

# print("\n # WEEK ", week, " POWER RANKINGS")
# league.printPowerRankings(week)

print("\n### LUCK INDEX")
league.printLuckIndex(week)

# print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " LOG WEIGHTED")
# print(table(logWeightedPS_prnt, headers='keys', tablefmt='github', numalign='decimal'))


# close text file
sys.stdout.close()
