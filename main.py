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
import re
import json

from utils.printing_utils import printPowerRankings

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the NFL season to run rankings for')
args = parser.parse_args()
week = int(args.week)

# Define user and season year
user_id = 'cgeer98'
year = datetime.now().year
month =  datetime.now().month
day = datetime.now().day

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

def gen_power_rankings():
    power_rankings = league.power_rankings(week=week)

    # Extract team names
    extracted_team_names = [(record, re.sub(r'Team\((.*?)\)', r'\1', str(team))) #convert team object to string
        for record, team in power_rankings]

    # Convert to Dataframe
    power_rankings = pd.DataFrame(extracted_team_names, columns=['Power Score','Team'])


    # Switch Score and Team Name cols
    power_rankings = power_rankings.reindex(columns=['Team', 'Power Score'])

    return power_rankings

def gen_ai_summary():
    # Retrieve all matchups for the given week
    matchups = league.box_scores(week=week)

    # Extract box score data
    box_scores_data = []

    for matchup in matchups:
        matchup_data = {
            "home_team": matchup.home_team.team_name,
            "home_score": matchup.home_score,
            "home_projected": matchup.home_projected,
            "away_team": matchup.away_team.team_name,
            "away_score": matchup.away_score,
            "away_projected": matchup.away_projected,
            "home_players": [
                {
                    "player_name": player.name,
                    "slot_position": player.slot_position,
                    "position": player.position,
                    "points": player.points,
                    "projected_points": player.projected_points
                } for player in matchup.home_lineup
            ],
            "away_players": [
                {
                    "player_name": player.name,
                    "position": player.position,
                    "slot_position": player.slot_position,
                    "points": player.points,
                    "projected_points": player.projected_points
                } for player in matchup.away_lineup
            ]
        }
        box_scores_data.append(matchup_data)

    # Convert to JSON format
    box_scores_json = json.dumps(box_scores_data, indent=4)

    print(box_scores_json)
    return(box_scores_json)
    
# Generate Power Rankings
rankings = gen_power_rankings()

# Generate Expected Standings

# Generate Playoff Probability (if week 5 or later) and append to expected standings

# Generate Luck Index

# Generate AI Summary
summary = gen_ai_summary()
print("\nFinal Summary:",summary)

# Print everything
# open text file
filepath = f"/Users/christiangeer/Fantasy_Sports/football/power_rankings/jtown-dynasty/content/blog/Week{week}{year}PowerRankings.md"
sys.stdout = open(filepath, "w")

# for the markdown files in blog
print("---")
print("title: Week", str(week), year, "Report")
print("date: ",datetime.now().date())
print(f"image: /images/{year}week{week}.jpeg")
print("draft: true")
print("---")

print("<!-- excerpt -->")

print("\n# POWER RANKINGS\n")
# Value un-informed
print(table(rankings, headers='keys', tablefmt='pipe', numalign='center')) # have to manually center all play % because its not a number

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
