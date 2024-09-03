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

# create list of the weekly scores for the season
seasonScores = []

for team in teams:
    weeklyScores = team.scores
    seasonScores.append(weeklyScores)
print(seasonScores)

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
for team in teams:
    wins = team.wins
    scores = team.scores
    print(scores)
    PF = sum(scores)
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

if week >= 5:
    print("\n# PLAYOFF PROBABILITIES (as of week ", week, ")")
    print(table(projections, headers='keys', tablefmt='pipe', numalign='center'))


# print("\n# LUCK INDEX")
# league.printLuckIndex(week)

# print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))

# close text file
sys.stdout.close()
