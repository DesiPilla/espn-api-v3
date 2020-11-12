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

# week = int(input("Enter Week:"))

teams = league.teams
teams_list = list(teams.values())
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
teams_list_df = pd.DataFrame(data=teams_list)
print(seasonScores_df)
print(teams_list_df)
teams_list_df.join(seasonScores_df)
# rosters_flat = list(chain.from_iterable(rosters))
# print(rosters_flat)

# print("\nFirst Roster:")
# print(rosters[1])
# print("\n Second Roster:")
# print(rosters[2])

# league.printPowerRankings(9)
# league.printLuckIndex(9)
