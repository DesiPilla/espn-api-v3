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

# import dynasty process values
dynastyProcessValues = pd.read_csv("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/data/files/values-players.csv")
dynastyProcessValues = dynastyProcessValues[["player","value_1qb"]]


# create for loop to add team names from team objects into list
teams = league.teams
teams_list = list(teams.values())
team_names = []
for team in teams_list:
    team_name = team.teamName
    team_names.append(team_name)

# create list of the weekly scores for the season
seasonScores = []

for team in teams_list:
    weeklyScores = team.scores
    seasonScores.append(weeklyScores)

# turn into dataframes
seasonScores_df = pd.DataFrame(data=seasonScores)
teams_names_df = pd.DataFrame(data=team_names,columns=['Team'])
team_scores = teams_names_df.join(seasonScores_df)

# get df headings for subsetting df
team_scores_headings = list(team_scores)

# get headings for up to selected week
current_week_headings = team_scores_headings[1:week+1]

# set the index to the team column for better indexing (.iloc)
team_scores = team_scores.set_index('Team')
scores = team_scores.copy()

# create a row for the league average for each week
team_scores.loc['League Average'] = (team_scores.sum(numeric_only=True, axis=0)/8).round(2)

# subract each teams score from the league average for that week
team_scores[:] = team_scores[:] - team_scores.loc['League Average']
team_scores = team_scores.drop("League Average") # leageue average no longer necessary
team_scores_log = team_scores.copy()


### LOG WEIGHTED RANKINGS


# new dataframe for the logged power score calculation
logged_ps = team_names.copy()
logged_ps = pd.DataFrame(logged_ps, columns=['team'])
logged_ps['lnPowerScore'] = 0
logged_ps = logged_ps.set_index('team')

column = []
tables = []
tables_names = team_names.copy()
tables_names = pd.DataFrame(tables_names, columns=["team"])

team_scores_log_col = list(team_scores_log[1:])
compute_week = 1 #

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


### 3 WEEK ROLLING AVERAGE RANKINGS


# get columns for calculating power score
last = current_week_headings[-1]
if len(current_week_headings) > 1:
    _2last = current_week_headings[-2]

if len(current_week_headings) > 2:
    _3last = current_week_headings[-3]

if len(current_week_headings) > 3:
    rest = current_week_headings[0:-3]


if len(current_week_headings) == 1: # for week 1, power score is just pf
    team_scores['Power_Score'] = (team_scores[last])
elif len(current_week_headings) == 2: # for week two avererage of first two weeks, week 2 a litter heavier wegiht
    team_scores['Power_Score'] = ((team_scores[last]*.6) + (team_scores[_2last])*.4)/1
elif len(current_week_headings) == 3: # for week 3 same wegihted average approach, but different wegihts
    team_scores['Power_Score'] = ((team_scores[last]*.25) + (team_scores[_2last]*.15) + (team_scores[_3last]*.1))/.5
else: # for the rest of the season
    team_scores['Power_Score'] = ((team_scores[last]*.3) + (team_scores[_2last]*.15) + (team_scores[_3last]*.1) + (team_scores[rest].mean(axis=1)*.45))/1

# sort by power socre
team_scores = team_scores.sort_values(by='Power_Score', ascending=False)

# 3 week rolling average
last_3 = current_week_headings[-3:]
team_scores['3_wk_roll_avg'] = (team_scores[last_3].sum(axis=1)/3).round(2)

# creating season average points column
season = list(team_scores)
season = season[1:-1]
team_scores['Season_avg'] = (team_scores[season].sum(axis=1)/week).round(2)

# for printing
team_scores_prt = team_scores['Power_Score'].round(2)
team_scores_prt = team_scores_prt.reset_index()
# team_scores_prt = team_scores.columns['team','Power Score']


### ALL PLAY POWER RANKINGS


allplay = team_names.copy()
allplay = pd.DataFrame(allplay,columns=['team'])

# add new columns to be filled by for loop
allplay['allPlayWins'] = 0
allplay['allPlayLosses'] = 0
allplay['PowerScore'] = 0
allplay = allplay.set_index('team')

# get headings of allplay table
allplay_head = list(allplay)

# set the initial week for the foor loop to 1
compare_week = current_week_headings[0]

# iterates over each item in the dataframe and compares to every team against one another, addng 1 for wins and losses
while compare_week <= week: # run until getting to current week
    for first_row in scores.itertuples():
        for second_row in scores.itertuples():
            if first_row[compare_week] > second_row[compare_week]:
                allplay.loc[first_row[0],allplay_head[0]] += 1 # add 1 to allplay wins
                allplay.loc[first_row[0],allplay_head[2]] += (1 + (math.log(compare_week))) # add log adjusted wins for power score
            elif first_row[compare_week] < second_row[compare_week]:
                allplay.loc[first_row[0],allplay_head[1]] += 1 # add 1 to allplay losses
            else:
                continue
    if compare_week == week-1: # create copy of the last week for weekly change calculations
        lw_allplay = allplay.copy()

    compare_week += 1

# create allplay win percentage
allplay['AllPlayWin%'] = allplay['allPlayWins'] / (allplay['allPlayWins'] + allplay['allPlayLosses'])
allplay['AllPlayWin%'] = allplay['AllPlayWin%'].round(3)

allplay = allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False) # Sort allplay by allplay wins with a powerscore tiebreaker
allplay['PowerScore'] = allplay['PowerScore'].round(2) # round powerscore to 2 decimal points
allplay = allplay.reset_index()

# create table for last week to compare for weekly change
lw_allplay = lw_allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False)
lw_allplay['PowerScore'] = lw_allplay['PowerScore'].round(2)
lw_allplay = lw_allplay.reset_index()

# create allplay table sorted by power score
allplay_ps = allplay.sort_values(by='PowerScore', ascending=False)
allplay_ps = allplay_ps.reset_index(drop=True)

# create allplay table sorted by power score
lw_allplay_ps = lw_allplay.sort_values(by='PowerScore', ascending=False)
lw_allplay_ps = lw_allplay_ps.reset_index(drop=True)

# create empty lists to add to in the for loop
diffs = []
emojis = []
emoji_names = allplay_ps['team'].tolist()

for team in emoji_names:
    tw_index = allplay_ps[allplay_ps['team'] == team].index.values # get index values of this weeks power rankigns
    lw_index = lw_allplay_ps[lw_allplay_ps['team'] == team].index.values  # get index values of last weeks power rankings
    diff = lw_index-tw_index # find the difference between last week to this week
    diff = int(diff.item()) # turn into list to iterate over
    diffs.append(diff) # append to the list

# iterate over diffs list and edit values to include up/down arrow emoji and the number of spots the team moved
for item in diffs:
    if item > 0:
        emojis.append("⬆️ " + str(abs(item)))
    elif item < 0:
        emojis.append("⬇️ " + str(abs(item)))
    elif item == 0:
        emojis.append("") # adds a index of nothing for teams that didn't move

allplay_ps.insert(loc=1, column='Weekly Change', value=emojis) # insert the weekly change column


### EXPCETED STANDINGS

allplay_es = allplay.copy() # creat copy of all play to be used for expected standings
allplay_es = allplay_es.set_index('team') # set the index to team for .loc

allScheduleProb = [] # empty list to be filled with win probabilties for each teams schedule

for team in teams_list:
    teamAP = allplay_es['AllPlayWin%'].loc[team.teamName] # Get each teams current All Play Win Percentage

    scheduleOBJ = list((team.schedule).values()) # get list of team objects
    scheduleProb = [] # tempory list to fill in inner for loop
    for opp in scheduleOBJ:
        oppAP = allplay_es['AllPlayWin%'].loc[opp.teamName]
        prob = teamAP / (oppAP + teamAP)
        scheduleProb.append(prob)
        # for values in key:
        #      schedule.append(item.teamName)
    allScheduleProb.append(scheduleProb) # append each team

allScheduleProb = pd.DataFrame(allScheduleProb)

probSched = pd.DataFrame(team_names, columns = ['Team'])

probSched = probSched.join(allScheduleProb)

weeksLeft = week - 13
probSchedLeft = probSched[probSched.columns[weeksLeft:]] # create dataframe of the prob schedules for weeks left to play

projectedStandings = pd.DataFrame(probSched['Team'].to_numpy(), columns=['Team']) # start projectedStandings with just team names

currentWins = []
currentLosses = []
# add current wins and losses to empty lists to be added to projectedStandings
for team in teams_list:
    currentWins = np.append(currentWins, team.wins)
    currentLosses = np.append(currentLosses, team.losses)

projectedStandings['CurrentWins'] = currentWins
projectedStandings['CurrentLosses'] = currentLosses

# sum up the probabilties to get proj wins and losses
projectedStandings['ForcastedWins'] = probSched.iloc[:, weeksLeft-2:-2].sum(axis=1).round(2)
projectedStandings['ForcastedLosses'] = abs(weeksLeft) - projectedStandings['ForcastedWins'].round(2)

# add projected and current wins to total projection
totalWinProj = projectedStandings['CurrentWins'] + projectedStandings['ForcastedWins']
totalLossProj = projectedStandings['CurrentLosses'] + projectedStandings['ForcastedLosses']

# insert total win and loss projections
projectedStandings.insert(loc=1, column='TotalProjWins', value=totalWinProj)
projectedStandings.insert(loc=2, column='TotalProjLoss', value=totalLossProj)

# sort and reset index
projectedStandings = projectedStandings.sort_values(by='TotalProjWins', ascending=False)
projectedStandings = projectedStandings.reset_index(drop=True)

projectedStandings_prnt = projectedStandings[]['TotalProjWins','TotalProjLoss']

# Set index for printing tables to start at 1
allplay.index = np.arange(1, len(allplay) + 1)
allplay_ps.index = np.arange(1, len(allplay_ps) + 1)
team_scores_prt.index = np.arange(1, len(team_scores_prt) + 1)
logWeightedPS_prnt.index = np.arange(1, len(logWeightedPS_prnt) + 1)
projectedStandings_prnt.index = np.arange(1, len(projectedStandings_prnt) + 1)


# # Print everything
# # open text file
# filepath = "/Users/christiangeer/Fantasy_Sports/Fantasy_FF/power_rankings/jtown-dynasty/content/blog/Week"+ str(week) + "PowerRankings.md"
# sys.stdout = open(filepath, "w")
#
# # for the markdown files in blog
# print("---")
# print("title: Week (WEEK) Report")
# print("date: 2020-MONTH-DAY")
# print("image: /images/week(ADD WEEK NUMBER HERE).jpg")
# print("draft: false")
# print("---")
#
# print("<!-- excerpt -->")
#
# print("\n### POWER RANKINGS\n")
# print(table(allplay_ps, headers='keys', tablefmt='github'))
#
# print("\n### EXPECTED STANDINGS (as of week ", week, ")")
# # league.printExpectedStandings(week)
#
#
# # print("\n # WEEK ", week, " POWER RANKINGS")
# # league.printPowerRankings(week)
#
# print("\n### LUCK INDEX")
# league.printLuckIndex(week)
#
# # print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# # print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))
#
# # print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# # print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))
#
# # print("\n WEEK ", week, " LOG WEIGHTED")
# # print(table(logWeightedPS_prnt, headers='keys', tablefmt='github', numalign='decimal'))
#
#
# # close text file
# sys.stdout.close()
