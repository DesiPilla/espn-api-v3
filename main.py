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

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the season')
args = parser.parse_args()
week = int(args.week)

# Define user and season year
user_id = 'cgeer98'
year = 2024

# Get login credentials for leagues
# login = pd.read_csv('C:\\Users\\desid\\Documents\\Fantasy_Football\\espn-api-v3\\login.csv')
# _, username, password, league_id, swid, espn_s2 = login[login['id'] == user_id].values[0]
username = 'cgeer98'
password = 'Penguins1!'
league_id = 916709
swid = '{75C7094F-C467-4145-8709-4FC467C1457E}'
espn_s2 = 'AEAldgr2G2n0JKOnYGii6ap3v4Yu03NjpuI2D0SSZDAMoUNm0y2DKP4GRofzL8sn%2Bzoc%2FAVwYxZ9Z9YvhFXPxZq9VE1d5KZIFOPQUWvx9mhdI0GJQUQU3OMid9SySbpzCI7K5hQ3LoxVAjqNT%2FvaIRy%2F7G8qm4l%2BL8fPBouCQI7k9W7c01T3J4RqFoQ3g%2B3ttyHKqhvg7DWDUkXNzJyxgFytKiRqah%2Fb77L67CD0bS7SFzFZPt%2BOrTohER9w8Lxoi0W0dAA%2BmqCfXzUTh9%2FEdxcf'

root = '/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/'

# Generate cookies payload and API endpoint
cookies = {'swid' : swid, 'espn_s2' : espn_s2}
url = getUrl(year, league_id)


league = League(league_id, year, espn_s2, swid)
print(league, "\n")
# import dynasty process values
# dynastyProcessValues = pd.read_csv("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/data/files/values-players.csv")
# dynastyProcessValues = dynastyProcessValues[["player","value_1qb"]]


# create for loop to add team names from team objects into list
teams = league.teams
# teams_list = list(teams.values())
teams_list = teams.copy()
team_names = teams.copy()
# for team in teams_list:
#     team_name = team.teamName
#     team_names.append(team_name)

# create list of the weekly scores for the season
seasonScores = []

for team in teams_list:
    weeklyScores = team.scores
    print("\nTeam: ", team, "\n", "weeklyScores", weeklyScores, "\n")
    seasonScores.append(weeklyScores)

# turn into dataframes
seasonScores_df = pd.DataFrame(data=seasonScores)
teams_names_df = pd.DataFrame(data=team_names,columns=['Team'])
team_scores = teams_names_df.join(seasonScores_df)

print("seasonScores: ", seasonScores)

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

#### 3 WEEK ROLLING AVERAGE RANKINGS


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
print("allplay_head:  ", allplay_head)
# set the initial week for the for loop to 1
compare_week = current_week_headings[0]
print("compare_week: ", compare_week)
# iterates over each item in the dataframe and compares to every team against one another, adding 1 for wins and losses
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
allplay['PowerScore'] = allplay['PowerScore'].round(1) # round powerscore to 1 decimal points
allplay = allplay.reset_index()

# create allplay table sorted by power score
allplay_ps = allplay[['team', 'AllPlayWin%', 'PowerScore']]
allplay_ps = allplay_ps.sort_values(by='PowerScore', ascending=False)
allplay_ps = allplay_ps.reset_index(drop=True)

allplay_ps['AllPlayWin%'] = (allplay_ps['AllPlayWin%'] * 100).round(2)
allplay_ps['AllPlayWin%'] = allplay_ps['AllPlayWin%'].astype(str) + "%"


# PLAYER VALUE POWER RANKINGS

# Load player values for last weeks starting lineup
player_values = playerID.get_player_values(week)
# print('player_values: \n', player_values)

# Group by team and average the values to get average team value

### TODO: Group by pos for analysis


# covnert rating to a float from object
player_values['rating'] = player_values['rating'].astype(str).astype(float)

# missing PLAYERS


# group by team and get the average rating of starters
# team_values = player_values.groupby('team').value_1qb.mean().reset_index()
team_values = player_values.groupby('team').rating.mean().reset_index()

# print('Week ', week, ' Team Values: \n', team_values)

# team_pos_values = team_pos_values[['team','position','salary','mean']].round(2)
# print(team_pos_values)

# Difference between team value and the top team value / team percent of total league value
# team_values['Value Diff'] = team_values['value_1qb'] - team_values['value_1qb'].max()
team_values['Value Diff'] = team_values['rating'] - team_values['rating'].max()
# print('team_values: \n', team_values)

# As a percent of the worst value (to get on same scale as Power Score)
team_values['% Value Diff'] = abs(team_values['Value Diff']) / team_values['Value Diff'].min()

# Calculate total value as a percent of the total league value
# team_values['% Total Value'] = team_values['value_1qb']/team_values['value_1qb'].sum()
team_values['% Total Value'] = team_values['rating']/team_values['rating'].sum()
team_values = team_values.round(2)

# team_values = team_values.sort_values(by = '% Total Value', ascending=False)
# Merge with Power Rankings to get PowerScore
allplay_ps_val = allplay_ps.merge(team_values, on='team')

# Calculate power score as percent of highest score
allplay_ps_val['% PowerScore'] = allplay_ps_val['PowerScore'] / allplay_ps_val['PowerScore'].max()
# allplay_ps_val['ps w/ values'] = allplay_ps_val['% PowerScore'] + allplay_ps_val['% Total Value']

# Unweighted rankings
allplay_ps_val['Ranked'] = allplay_ps_val['% PowerScore'] + allplay_ps_val['% Value Diff']
allplay_ps_val['Ranked clean'] = allplay_ps_val['Ranked'] + abs(allplay_ps_val['Ranked'].min())

# Weighted rankings
allplay_ps_val['Weighted Avg'] = (allplay_ps_val['% PowerScore']*.60) + (allplay_ps_val['% Value Diff']*.40)
allplay_ps_val.reset_index()
# allplay_ps_val['Weighted Avg'] = (allplay_ps_val['% PowerScore']*.60) + (allplay_ps_val['% Total Value']*.40)
# allplay_ps_val['Weighted Avg'] = allplay_ps_val['Weighted Avg'] + abs(allplay_ps_val['Weighted Avg'].min())

# Rank and print values for analysis
Value_Power_Rankings = allplay_ps_val[['team','AllPlayWin%','% PowerScore','% Value Diff', '% Total Value','Weighted Avg']].sort_values(by='Weighted Avg', ascending=False).reset_index(drop=True)
Value_Power_Rankings_rank = allplay_ps_val[['% PowerScore','% Value Diff','% Total Value', 'Weighted Avg']].rank(ascending=False, method='min')
Value_Power_Rankings_rank.insert(loc=0, column='AllPlayWin%', value=allplay['allPlayWins'] / (allplay['allPlayWins'] + allplay['allPlayLosses']))
Value_Power_Rankings_rank.insert(loc=0, column='Team',value=allplay_ps_val['team'])
Value_Power_Rankings_rank['AllPlayWin%'] = Value_Power_Rankings_rank['AllPlayWin%'].rank(ascending=False, method='min')

print("\nValue Power Rankings: \n", allplay_ps_val[['team','AllPlayWin%','% PowerScore','% Value Diff', '% Total Value','Weighted Avg']].sort_values(by='Weighted Avg', ascending=False).reset_index(drop=True))
print("\nValue Power Rankings Ranks: \n", Value_Power_Rankings_rank.sort_values(by = 'Weighted Avg').reset_index(drop=True), "\n")

Value_Power_Rankings_print = allplay_ps_val[['team','AllPlayWin%','Weighted Avg']].sort_values(by=['Weighted Avg','AllPlayWin%'], ascending=False)
Value_Power_Rankings_print['Weighted Avg'] = (Value_Power_Rankings_print['Weighted Avg']*100).round(2)
Value_Power_Rankings_print = Value_Power_Rankings_print.rename(columns={'Weighted Avg':'Value Power Score'})

print('Week ', week, ' Rosters NaN: \n', player_values[player_values['rating'].isna()])

# Value_Power_Rankings_print.index = np.arange(1, len(Value_Power_Rankings_print) + 1)
Value_Power_Rankings_print.to_csv('/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/past_rankings/week' + str(week) + '.csv')

# Create last week value informed power rankings
if week > 1:
    # Load player values for previous week starting lineup
    lw_player_values = pd.read_csv('/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/values/week' + str(week-1) + '.csv')

    # missingPlayer = ['Chuba Hubbard','5.09','+1.3']
    lw_player_values.loc[(lw_player_values.player == 'Damien Williams'), 'rating'] = '8.18'

    # missing = pd.DataFrame([missingPlayer],columns=['player','rating','change'])
    # lw_player_values = lw_player_values.append(missing, ignore_index=True)
    #
    # missing = pd.DataFrame([missingPlayer2],columns=['player','rating','change'])
    # lw_player_values = lw_player_values.append(missing, ignore_index=True)

    print('\nWeek ', week-1, ' Rosters NaN: \n', lw_player_values[lw_player_values['rating'].isna()])

    # covnert rating to a float from object
    lw_player_values['rating'] = lw_player_values['rating'].astype(str).astype(float)

    # Group by team and average the values to get average team value
    # lw_team_values = lw_player_values.groupby('team').value_1qb.mean().reset_index()
    lw_team_values = lw_player_values.groupby('team').rating.mean().reset_index()

    # Difference between team value and the top team value
    # lw_team_values['Value Diff'] = lw_team_values['value_1qb'] - lw_team_values['value_1qb'].max()
    lw_team_values['Value Diff'] = lw_team_values['rating'] - lw_team_values['rating'].max()
    # print('lw_team_values: \n', lw_team_values)

    # As a percent of the worst value (to get on same scale as Power Score) OR % of total league value
    lw_team_values['% Value Diff'] = abs(lw_team_values['Value Diff']) / lw_team_values['Value Diff'].min()
    # lw_team_values['% Total Value'] = lw_team_values['value_1qb'] / lw_team_values['value_1qb'].sum()
    lw_team_values['% Total Value'] = lw_team_values['rating'] / lw_team_values['rating'].sum()

    # Merge with Power Rankings to get PowerScore
    lw_allplay.reset_index() #reset the index so we can merge on team
    lw_allplay_ps_val = lw_allplay.merge(lw_team_values, on='team')

    # Calculate power score as percent of highest score
    lw_allplay_ps_val['% PowerScore'] = lw_allplay_ps_val['PowerScore'] / lw_allplay_ps_val['PowerScore'].max()

    # Weighted rankings
    lw_allplay_ps_val['Weighted Avg'] = (lw_allplay_ps_val['% PowerScore']*.60) + (lw_allplay_ps_val['% Value Diff']*.40)
    # lw_allplay_ps_val['Weighted Avg'] = (lw_allplay_ps_val['% PowerScore']) + (lw_allplay_ps_val['% Total Value'])
    # lw_allplay_ps_val['Weighted Avg'] = lw_allplay_ps_val['Weighted Avg'] + abs(lw_allplay_ps_val['Weighted Avg'].min())
    lw_allplay_ps_val = lw_allplay_ps_val.sort_values(by='Weighted Avg', ascending=False).reset_index()

    # print("lw_allplay_ps_val \n", lw_allplay_ps_val[['team','% Value Diff','% PowerScore','Weighted Avg']])

# Print current and last week team values for evaluation
print("\nThis Week Team Values:\n", team_values.sort_values(by='rating',ascending=False))
print("\nLast Week Team Values:\n", lw_team_values.sort_values(by='rating',ascending=False).round(2))


if week > 1:

    # # create table for last week to compare for weekly change
    # lw_allplay = lw_allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False)
    # lw_allplay['PowerScore'] = lw_allplay['PowerScore'].round(2)
    # lw_allplay = lw_allplay.reset_index()

    # DEPRACATED

    # # create table for last week to compare for weekly change with Value Informed Rankings
    # lw_allplay_compare = lw_allplay_ps_val[['team','Weighted Avg']].sort_values(by=['Weighted Avg'], ascending=False)
    # lw_allplay_compare['Weighted Avg'] = lw_allplay_compare['Weighted Avg'].round(4)
    # lw_allplay_compare = lw_allplay_compare.reset_index(drop=True)

    # # create allplay table sorted by power score
    # lw_allplay_ps = lw_allplay.sort_values(by='PowerScore', ascending=False)
    # lw_allplay_ps = lw_allplay_ps.reset_index(drop=True)

    # # create empty lists to add to in the for loop
    # diffs = []
    # emojis = []
    # emoji_names = allplay_ps['team'].tolist()
    #
    # for team in emoji_names:
    #     tw_index = allplay_ps[allplay_ps['team'] == team].index.values # get index values of this weeks power rankigns
    #     lw_index = lw_allplay_ps[lw_allplay_ps['team'] == team].index.values  # get index values of last weeks power rankings
    #     diff = lw_index-tw_index # find the difference between last week to this week
    #     diff = int(diff.item()) # turn into list to iterate over
    #     diffs.append(diff) # append to the list
    #
    # # iterate over diffs list and edit values to include up/down arrow emoji and the number of spots the team moved
    # for item in diffs:
    #     if item > 0:
    #         emojis.append("**<span style=\"color: green;\">⬆️ " + str(abs(item)) + " </span>**" )
    #     elif item < 0:
    #         emojis.append("**<span style=\"color: red;\">⬇️ " + str(abs(item)) + " </span>**")
    #     elif item == 0:
    #         emojis.append("") # adds a index of nothing for teams that didn't move
    #
    # allplay_ps.insert(loc=1, column='Weekly Change', value=emojis) # insert the weekly change column

    # create empty lists to add to in the for loop (Value Informed Ranking)
    diffs = []
    emojis = []
    emoji_names = Value_Power_Rankings['team'].tolist()

    tw_rankings = pd.read_csv(root + 'past_rankings/week' + str(week) + '.csv')
    lw_rankings = pd.read_csv(root + 'past_rankings/week' + str(week-1) + '.csv')

    print('This week: \n', tw_rankings)
    print('Last week: \n', lw_rankings)

    for team in emoji_names:
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

### EXPCETED STANDINGS

#### TODO: Update to use the new Value Informed Power Rankings instead of just AllPlayWin%

# allplay_es = allplay.copy() # creat copy of all play to be used for expected standings
# allplay_es = allplay_es.set_index('team') # set the index to team for .loc

# new dataframe for expected standings
ValuePowerRankings_ES = allplay_ps_val[['team','Weighted Avg']]
ValuePowerRankings_ES = ValuePowerRankings_ES.set_index('team')

# move everything to positive
ValuePowerRankings_ES['Weighted Avg'] = ValuePowerRankings_ES['Weighted Avg'] + abs(ValuePowerRankings_ES['Weighted Avg'].min())


allScheduleProb = [] # empty list to be filled with win probabilties for each teams schedule
sos = [] # strength of schedule list

for team in teams_list:
    # teamAP = allplay_es['AllPlayWin%'].loc[team.teamName] # Get each teams current All Play Win Percentage
    teamPS = ValuePowerRankings_ES['Weighted Avg'].loc[team.teamName] # Get each teams current All Play Win Percentage

    scheduleOBJ = list((team.schedule).values()) # get list of team objects
    scheduleProb = [] # tempory list to fill in inner for loop
    teamSOS = 0 # initialize to 0 for each team
    for opp in scheduleOBJ:
        # oppAP = allplay_es['AllPlayWin%'].loc[opp.teamName]
        # prob = teamAP / (oppAP + teamAP)

        oppPS = ValuePowerRankings_ES['Weighted Avg'].loc[opp.teamName]
        prob = teamPS / (oppPS + teamPS)

        teamSOS += oppPS
        scheduleProb.append(prob)
        # for values in key:
        #      schedule.append(item.teamName)
    allScheduleProb.append(scheduleProb) # append each team
    addToSOS = [team.teamName, teamSOS]
    sos.append(addToSOS) # append each team's SOS

# convert to pandas dataframes
allScheduleProb = pd.DataFrame(allScheduleProb)
sos = pd.DataFrame(sos).round(2)

sos = sos.iloc[:,0:2] # remove empty end column
sos = sos.set_axis(['Team', 'SOS'], axis=1, inplace=False) # set column names

probSched = pd.DataFrame(team_names, columns = ['Team'])

probSched = probSched.join(allScheduleProb)

weeksLeft = week - 15
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

projectedStandings_prnt = projectedStandings[['Team','TotalProjWins','TotalProjLoss']]

# if week >= 9:
#     # Merge in SOS
#     projectedStandings_prnt = projectedStandings_prnt.merge(sos, on='Team')

## MONTE CARLO PLAYOFF PROBABILIIES


#number of random season's to simulate
simulations = 1000000
#weeks in the regular season
league_weeks = 15
#number of teams to playoffs
teams_to_play_off = 4

#team_names:: list of team names. list order is used to
#index home_teams and away_teams

#home_teams, away_teams: list of remaining matchups in the regular season.
#Indexes are based on order from team_names

#current_wins: Integer value represents each team's win count.
#The decimal is used to further order teams based on points for eg 644.8 points would be 0.006448.
#Order needs to be the same as team_names

# teams already added to list in code above
# ['Pat'[1], 'Trevor'[2], 'Billy'[3], 'Jack'[4], 'Travis'[5], 'Lucas'[6], 'Cade'[7], 'Christian'[8]]

# Remaining schedule (week 5 and on)
home_teams = [8,5,4,6,3,1,7,2,1,7,3,2,6,3,2,4,8,2,1,4,8,3,1,6,8,5,4,6,7,3,2,1,8,5,4,1,1,3,2,7,2,3,7,1]
away_teams = [7,1,2,3,8,6,4,5,8,5,4,6,8,1,7,5,5,3,7,6,4,7,2,5,2,3,1,7,8,6,4,5,3,2,7,6,8,4,6,5,8,4,6,5]

# only update current wins at week 5
# don't need to do below, taken care of in for loop
# current_wins = [2.010742,3.011697,7.013179,2.010177,6.011863,1.010001,6.012642,5.011502]
current_wins = []
for team in teams_list:
    wins = team.wins
    scores = team.scores
    PF = sum(scores.values())
    PF = round(PF, 2)
    PF = PF/100000
    current_wins.append(wins + PF)

###ONLY CONFIGURE THE VALUES ABOVE

if week >= 5:
    teams = [int(x) for x in range(1,len(team_names)+1)]
    weeks_played = (league_weeks)-((len(home_teams))/(len(teams)/2))


    last_playoff_wins = [0] * (league_weeks)
    first_playoff_miss = [0] * (league_weeks)

    import datetime

    begin = datetime.datetime.now()
    import random


    league_size = len(teams)


    games_per_week = int(league_size/2)
    weeks_to_play = int(league_weeks-weeks_played)
    total_games = int(league_weeks * games_per_week)
    games_left = int(weeks_to_play * games_per_week)

    stats_teams = [0] * (league_size)


    play_off_matrix = [[0 for x in range(teams_to_play_off)] for x in range(league_size)]

    pad = int(games_left)

    avg_wins = [0.0] * teams_to_play_off


    for sims in progressbar.progressbar(range(1,simulations+1)):
        #create random binary array representing a single season's results
        val = [int(random.getrandbits(1)) for x in range(1,(games_left+1))]

        empty_teams = [0.0] * league_size

        i = 0
        #assign wins based on 1 or 0 to home or away team
        for x in val:
            if (val[i] == 1):
                empty_teams[home_teams[i]-1] = empty_teams[home_teams[i]-1]+1
            else:
                empty_teams[away_teams[i]-1] = empty_teams[away_teams[i]-1]+1
            i=i+1

        #add the current wins to the rest of season's results
        empty_teams = [sum(x) for x in zip(empty_teams,current_wins)]

        #sort the teams
        sorted_teams = sorted(empty_teams)



        last_playoff_wins[int(round(sorted_teams[(league_size-teams_to_play_off)],0))-1] = last_playoff_wins[int(round(sorted_teams[(league_size-teams_to_play_off)],0))-1] + 1
        first_playoff_miss[int(round(sorted_teams[league_size-(teams_to_play_off+1)],0))-1] = first_playoff_miss[int(round(sorted_teams[league_size-(teams_to_play_off+1)],0))-1] + 1



        #pick the teams making the playoffs
        for x in range(1,teams_to_play_off+1):
            stats_teams[empty_teams.index(sorted_teams[league_size-x])] = stats_teams[empty_teams.index(sorted_teams[league_size-x])] + 1
            avg_wins[x-1] = avg_wins[x-1] + round(sorted_teams[league_size-x],0)
            play_off_matrix[empty_teams.index(sorted_teams[league_size-x])][x-1] = play_off_matrix[empty_teams.index(sorted_teams[league_size-x])][x-1] + 1

    projections = []

    playSpots = []

    for x in range(1,len(stats_teams)+1):
        vals = ''
        for y in range(1,teams_to_play_off+1):
            vals = vals +'\t'+str(round((play_off_matrix[x-1][y-1])/simulations*100.0,2))

            playSpots.append(round((play_off_matrix[x-1][y-1])/simulations*100.0,2))

        playProb = round((stats_teams[x-1])/simulations*100.0,2)
        playSpots.insert(0, playProb)
        # print("Vals: ", playSpots)
        projections.append(playSpots)
        playSpots = []
        # print(team_names[x-1]+'\t'+str(round((stats_teams[x-1])/simulations*100.0,2))+vals)

    projections = pd.DataFrame(projections)
    projections.insert(loc=0, column='Team', value=team_names)
    projections = projections.set_axis(['Team', 'Playoffs', '1st Seed', '2nd Seed', '3rd Seed', '4th Seed'], axis=1, inplace=False)
    projections = projections.sort_values(by=['Playoffs','1st Seed', '2nd Seed', '3rd Seed', '4th Seed'], ascending=False)
    # projections[['1st Seed','2nd Seed','3rd Seed', '4th Seed']] = projections[['1st Seed','2nd Seed','3rd Seed', '4th Seed']].astype(str) + "%"
    projections.index = np.arange(1, len(projections) + 1)

    median = projections['Playoffs'].median()

    # bold only the playoff teams
    for index, row in projections.iterrows():
        if row['Playoffs'] > median:
            projections.loc[index, 'Team'] = '**' + str(row['Team']) + '**'
            projections.loc[index, 'Playoffs'] = '**' + str(row['Playoffs']) + '%**'
            projections.loc[index, '1st Seed'] = '**' + str(row['1st Seed']) + '%**'
            projections.loc[index, '2nd Seed'] = '**' + str(row['2nd Seed']) + '%**'
            projections.loc[index, '3rd Seed'] = '**' + str(row['3rd Seed']) + '%**'
            projections.loc[index, '4th Seed'] = '**' + str(row['4th Seed']) + '%**'
        else:
            projections.loc[index, 'Playoffs'] = str(row['Playoffs']) + '%'
            projections.loc[index, '1st Seed'] = str(row['1st Seed']) + '%'
            projections.loc[index, '2nd Seed'] = str(row['2nd Seed']) + '%'
            projections.loc[index, '3rd Seed'] = str(row['3rd Seed']) + '%'
            projections.loc[index, '4th Seed'] = str(row['4th Seed']) + '%'

    print('')

    # print('Average # of wins for playoff spot')
    # for x in range(1,teams_to_play_off+1):
    #     print(str(x)+'\t'+str(round((avg_wins[x-1])/simulations,2)))


    delta = datetime.datetime.now() - begin

    # print('')
    # print('Histrogram of wins required for final playoff spot')
    # for x in range(1,len(last_playoff_wins)+1):
    #     print(str(x)+'\t'+str(round((last_playoff_wins[x-1])/(simulations*1.0)*100,3))+'\t'+str(round((first_playoff_miss[x-1])/(simulations*1.0)*100,3)))


    print('\n{0:,}'.format(simulations) +" Simulations ran in "+str(delta))

# Set index for printing tables to start at 1
allplay.index = np.arange(1, len(allplay) + 1)
allplay_ps.index = np.arange(1, len(allplay_ps) + 1)
if week >5:
    projections.index = np.arange(1, len(projections) + 1)
team_scores_prt.index = np.arange(1, len(team_scores_prt) + 1)
projectedStandings_prnt.index = np.arange(1, len(projectedStandings_prnt) + 1)
Value_Power_Rankings_print.index = np.arange(1, len(Value_Power_Rankings) + 1)


# Print everything
# open text file
filepath = "/Users/christiangeer/Fantasy_Sports/football/power_rankings/jtown-dynasty/content/blog/Week"+ str(week) + str(year) + "PowerRankings.md"
sys.stdout = open(filepath, "w")

# for the markdown files in blog
print("---")
print("title: Week " + str(week) + " 2021 Report")
print("date: 2020-MONTH-DAY")
print("image: /images/2021week" + str(week) + ".jpeg")
print("draft: false")
print("---")

print("<!-- excerpt -->")

print("\n# POWER RANKINGS\n")
# Value un-informed
# print(table(allplay_ps, headers='keys', tablefmt='pipe', numalign='center')) # have to manually center all play % because its not a number

# Value Informed
print(table(Value_Power_Rankings_print, headers='keys',tablefmt='pipe', numalign='center')) # have to manually center all play % and weekly change because not an int

print('\n##Highlights:\n')

print("\n# EXPECTED STANDINGS (as of week ", week, ")")
# league.printExpectedStandings(week)
print(table(projectedStandings_prnt, headers='keys', tablefmt='pipe', numalign='center'))

if week >= 5:
    print("\n# PLAYOFF PROBABILITIES (as of week ", week, ")")
    print(table(projections, headers='keys', tablefmt='pipe', numalign='center'))


print("\n# LUCK INDEX")
league.printLuckIndex(week)

# print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))

# close text file
sys.stdout.close()
