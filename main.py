from league import League
from authorize import Authorize
from team import Team
from player import Player
from utils.building_utils import getUrl
from itertools import chain

import pandas as pd
import requests
from tabulate import tabulate as table

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

week = int(input("Enter Week:"))

# create for loop to add team names from team objects into list
teams = league.teams
teams_list = list(teams.values())
team_names = []
for team in teams_list:
    team_name = team.teamName
    team_names.append(team_name)

# rosters = []
# namesRoster = []
seasonScores = []

# team = league.teams[1]
# print(team)
# print(team.rosters[week])

for team in teams_list:
    weeklyScores = team.scores
    # for player in weeklyRoster:
    #     namesRoster.append(player.name)
    seasonScores.append(weeklyScores)

seasonScores_df = pd.DataFrame(data=seasonScores)
teams_names_df = pd.DataFrame(data=team_names,columns=['Team'])
team_scores = teams_names_df.join(seasonScores_df)

print(team_scores)

# set the index to the team column
team_scores = team_scores.set_index('Team')

# create a row for the league average for each week
team_scores.loc['League Average'] = (team_scores.sum(numeric_only=True, axis=0)/8).round(2)

# create a copy to not subract league Average
team_scores_noavg = team_scores.copy()

# subract each teams score from the league average for that week
team_scores[:] = team_scores[:] - team_scores.loc['League Average']
team_scores = team_scores.drop("League Average") # leageue average no longer necessary

# creating 3 week rolling average column
team_scores_headings = list(team_scores)
noavg_headings = list(team_scores_noavg)


# get columns for calculating power score
last = team_scores_headings[-1]
_2last = team_scores_headings[-2]
_3last = team_scores_headings[-3]
rest = team_scores_headings[0:-3]

last_nv = noavg_headings[-1]
_2last_nv = noavg_headings[-2]
_3last_nv = noavg_headings[-3]
rest_nv = noavg_headings[0:-3]

team_scores['Power_Score'] = (team_scores[last]*.25) + (team_scores[_2last]*.15) + (team_scores[_3last]*.1) + (team_scores[rest].mean(axis=1)*.5)/1
team_scores_noavg['Power_Score'] = (team_scores_noavg[last]*.25) + (team_scores[_2last_nv]*.15) + (team_scores[_3last_nv]*.1) + (team_scores[rest_nv].mean(axis=1)*.5)/1

team_scores = team_scores.sort_values(by='Power_Score', ascending=False)
team_scores_noavg = team_scores_noavg.sort_values(by='Power_Score', ascending=False)

last_3 = team_scores_headings[-3:]
team_scores['3_wk_roll_avg'] = (team_scores[last_3].sum(axis=1)/3).round(2)

# creating season average column
season = list(team_scores)
season = season[1:-1]
team_scores['Season_avg'] = (team_scores[season].sum(axis=1)/week).round(2)

print(team_scores[['Power_Score','3_wk_roll_avg','Season_avg']])


league.printPowerRankings(week)
league.printLuckIndex(week)
league.printExpectedStandings(week)
