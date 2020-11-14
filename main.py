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

week = int(input("\n Enter Week: "))

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


# Print everything
# open text file
sys.stdout = open("powerrankings.pdf", "w")

print("\n WEEK ", week, " POWER RANKINGS")
league.printPowerRankings(week)
print("\n WEEK ", week, " LUCK INDEX")
league.printLuckIndex(week)
print("\n WEEK ", week, " EXPECTED STANDINGS")
league.printExpectedStandings(week)
print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
print(table(allplay, headers='keys', tablefmt='simple', numalign='decimal'))
print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY POWER SCORE)")
print("\n", table(allplay_ps, headers='keys', tablefmt='simple'))
print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
print("\n", table(team_scores_prt, headers='keys', tablefmt='simple', numalign='decimal'))

# close text file
sys.stdout.close()

pdf = FPDF()
# Add a page
pdf.add_page()
# set style and size of font
# that you want in the pdf
pdf.set_font("Arial", size = 15)
# open the text file in read mode
f = open("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/power_rankings/espn-api-v3/powerrankings.txt", "r")
# insert the texts in pdf
for x in f:
    pdf.cell(50,5, txt = x, ln = 1, align = 'C')
# save the pdf with name .pdf
pdf.output("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/power_rankings/espn-api-v3\\powerrankings.pdf")
