from league import League
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
from fpdf import FPDF
import argparse
import progressbar

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the season')
args = parser.parse_args()
week = int(args.week)

# Define user and season year
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



# Generate cookies payload and API endpoint
cookies = {'swid' : swid, 'espn_s2' : espn_s2}
url = getUrl(year, league_id)


league = League(league_id, year, username, password, swid, espn_s2)
print(league, "\n")
# import dynasty process values
# dynastyProcessValues = pd.read_csv("/Users/christiangeer/Fantasy_Sports/Fantasy_FF/data/files/values-players.csv")
# dynastyProcessValues = dynastyProcessValues[["player","value_1qb"]]


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

# Group by team and average the values to get average team value
groupby_teams = player_values.groupby('team')
team_values = player_values.groupby('team').value_1qb.mean().reset_index()

# Difference between team value and the top team value
team_values['Value Diff'] = team_values['value_1qb'] - team_values['value_1qb'].max()

# As a percent of the worst value (to get on same scale as Power Score)
team_values['% Value Diff'] = abs(team_values['Value Diff']) / team_values['Value Diff'].min()

# Calculate total value as a percent of the highest value team
team_values['% Total Value'] = team_values['value_1qb']/team_values['value_1qb'].max()
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
# allplay_ps_val['Weighted Avg'] = allplay_ps_val['Weighted Avg'] + abs(allplay_ps_val['Weighted Avg'].min())

# Rank and print values for analysis
Value_Power_Rankings = allplay_ps_val[['% PowerScore','% Value Diff', 'Weighted Avg']].rank(ascending=False, method='min')
Value_Power_Rankings.insert(loc=0, column='AllPlayWin%', value=allplay['allPlayWins'] / (allplay['allPlayWins'] + allplay['allPlayLosses']))
Value_Power_Rankings.insert(loc=0, column='Team',value=allplay_ps_val['team'])
Value_Power_Rankings['AllPlayWin%'] = Value_Power_Rankings['AllPlayWin%'].rank(ascending=False, method='min')

print("\nValue Power Rankings: \n", allplay_ps_val[['team','AllPlayWin%','% PowerScore','% Value Diff','Weighted Avg']].sort_values(by='Weighted Avg', ascending=False))
print("\nValue Power Rankings Ranks: \n", Value_Power_Rankings.sort_values(by = 'Weighted Avg'), "\n")

Value_Power_Rankings_print = allplay_ps_val[['team','AllPlayWin%','Weighted Avg']].sort_values(by='Weighted Avg', ascending=False)
Value_Power_Rankings_print['Weighted Avg'] = (Value_Power_Rankings_print['Weighted Avg']*100).round(2)
# Value_Power_Rankings_print.rename(columns={'team':'Team'}, inplace=True)

# Create last week value informed power rankings
if week > 1:
    # Load player values for previous week starting lineup
    lw_player_values = playerID.get_player_values_lw(week-1)

    # Group by team and average the values to get average team value
    lw_groupby_teams = lw_player_values.groupby('team')
    lw_team_values = lw_player_values.groupby('team').value_1qb.mean().reset_index()

    # Difference between team value and the top team value
    lw_team_values['Value Diff'] = lw_team_values['value_1qb'] - lw_team_values['value_1qb'].max()

    # As a percent of the worst value (to get on same scale as Power Score)
    lw_team_values['% Value Diff'] = abs(lw_team_values['Value Diff']) / lw_team_values['Value Diff'].min()

    # Merge with Power Rankings to get PowerScore
    lw_allplay.reset_index() #reset the index so we can merge on team
    lw_allplay_ps_val = lw_allplay.merge(team_values, on='team')

    # Calculate power score as percent of highest score
    lw_allplay_ps_val['% PowerScore'] = lw_allplay_ps_val['PowerScore'] / lw_allplay_ps_val['PowerScore'].max()

    # Weighted rankings
    lw_allplay_ps_val['Weighted Avg'] = (lw_allplay_ps_val['% PowerScore']*.60) + (lw_allplay_ps_val['% Value Diff']*.40)
    lw_allplay_ps_val['Weighted Avg'] = lw_allplay_ps_val['Weighted Avg'] + abs(lw_allplay_ps_val['Weighted Avg'].min())


if week > 1:

    # # create table for last week to compare for weekly change
    # lw_allplay = lw_allplay.sort_values(by=['allPlayWins','PowerScore'], ascending=False)
    # lw_allplay['PowerScore'] = lw_allplay['PowerScore'].round(2)
    # lw_allplay = lw_allplay.reset_index()

    # create table for last week to compare for weekly change with Value Informed Rankings
    lw_allplay_compare = lw_allplay_ps_val['team','Weighted Avg'].sort_values(by=['Wegighted Avg'], ascending=False)
    lw_allplay_compare['Weighted Avg'] = lw_allplay_compare['Weighted Avg'].round(2)
    lw_allplay_compare = lw_allplay_compare.reset_index()

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
    emoji_names = Value_Power_Rankings['Team'].tolist()

    for team in emoji_names:
        tw_index = Value_Power_Rankings[Value_Power_Rankings['Team'] == team].index.values # get index values of this weeks power rankigns
        lw_index = lw_allplay_compare[lw_allplay_compare['Team'] == team].index.values  # get index values of last weeks power rankings
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

ValuePowerRankings_ES = allplay_ps_val[['team','Weighted Avg']]
ValuePowerRankings_ES = ValuePowerRankings_ES.set_index('team')

allScheduleProb = [] # empty list to be filled with win probabilties for each teams schedule

for team in teams_list:
    # teamAP = allplay_es['AllPlayWin%'].loc[team.teamName] # Get each teams current All Play Win Percentage
    teamPS = ValuePowerRankings_ES['Weighted Avg'].loc[team.teamName] # Get each teams current All Play Win Percentage

    scheduleOBJ = list((team.schedule).values()) # get list of team objects
    scheduleProb = [] # tempory list to fill in inner for loop
    for opp in scheduleOBJ:
        # oppAP = allplay_es['AllPlayWin%'].loc[opp.teamName]
        # prob = teamAP / (oppAP + teamAP)

        oppPS = ValuePowerRankings_ES['Weighted Avg'].loc[opp.teamName]
        prob = teamPS / (oppPS + teamPS)

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

projectedStandings_prnt = projectedStandings[['Team','TotalProjWins','TotalProjLoss']]


## MONTE CARLO PLAYOFF PROBABILIIES


#number of random season's to simulate
simulations = 1000000
#weeks in the regular season
league_weeks = 13
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
home_teams = [3,1,7,2,8,5,4,6,6,3,2,4,8,2,1,4,8,3,1,6,8,5,4,6,7,3,2,1,8,5,4,1]
away_teams = [8,6,4,5,1,7,3,2,8,1,7,5,5,3,7,6,4,7,2,5,2,3,1,7,8,6,4,5,3,2,7,6]

# only update current wins at week 5
# current_wins = [6.013909,6.014544,7.014027,5.014112,8.016490,3.012880,1.011269,4.012954]
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
    projections[['1st Seed','2nd Seed','3rd Seed', '4th Seed']] = projections[['1st Seed','2nd Seed','3rd Seed', '4th Seed']].astype(str) + "%"
    projections['Playoffs'] = "**" + projections['Playoffs'].astype(str) + "%**"

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
projections.index = np.arange(1, len(projections) + 1)
team_scores_prt.index = np.arange(1, len(team_scores_prt) + 1)
logWeightedPS_prnt.index = np.arange(1, len(logWeightedPS_prnt) + 1)
projectedStandings_prnt.index = np.arange(1, len(projectedStandings_prnt) + 1)
Value_Power_Rankings_print.index = np.arange(1, len(Value_Power_Rankings) + 1)


# Print everything
# open text file
filepath = "/Users/christiangeer/Fantasy_Sports/football/power_rankings/jtown-dynasty/content/blog/Week"+ str(week) + str(year) + "PowerRankings.md"
sys.stdout = open(filepath, "w")

# for the markdown files in blog
print("---")
print("title: Week (WEEK) (YEAR) Report")
print("date: 2020-MONTH-DAY")
print("image: /images/(YEAR)week(ADD WEEK NUMBER HERE).jpg")
print("draft: false")
print("---")

print("<!-- excerpt -->")

print("\n### POWER RANKINGS\n")
# Value un-informed
# print(table(allplay_ps, headers='keys', tablefmt='pipe', numalign='center')) # have to manually center all play % because its not a number

# Value Informed
print(table(Value_Power_Rankings_print, headers=['Team','All Play Win %','Value Power Score'],tablefmt='pipe', numalign='center')) # have to manually center all play % because its not a number

# print("\n### WEEK ", week, " POWER RANKINGS")
# league.printPowerRankings(week)

print("\n### EXPECTED STANDINGS (as of week ", week, ")")
# league.printExpectedStandings(week)
print(table(projectedStandings_prnt, headers='keys', tablefmt='pipe', numalign='center'))

if week >= 5:
    print("\n### PLAYOFF PROBABILITIES (as of week ", week, ")")
    print(table(projections, headers='keys', tablefmt='pipe', numalign='center'))


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
