'''
TODO:
1. Fix expected standings
2. Clean up code (value rankings)
3. Luck Index
'''
from langchain_core.runnables import RunnableSequence

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
import openai
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from utils.printing_utils import printPowerRankings
import os
from dotenv import load_dotenv

parser = argparse.ArgumentParser()
parser.add_argument("week", help='Get week of the NFL season to run rankings for')
args = parser.parse_args()
week = int(args.week)

# Define dates/year
year = datetime.now().year
month =  datetime.now().month
day = datetime.now().day

# Load environment variables from .env file
load_dotenv()

# Get login credentials for leagues
league_id = os.getenv('league_id')
swid = os.getenv('swid')
espn_s2 = os.getenv('espn_s2')
api_key= os.getenv('OPEN_AI_KEY')

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


    # Sample JSON data (replace with your actual JSON data)
    json_data = box_scores_json

    # Setting up OpenAI model
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0, openai_api_key=api_key)

    # Define the prompt template for generating a newspaper-like summary
    prompt_template = PromptTemplate(
        input_variables=["json_data"],
        template="""
        Write a newspaper-style summary of the fantasy football matchups based on the following JSON data:

        {json_data}

        The summary should include:
        - The names of the teams
        - The projected scores for each team
        - Key players and their projected points
        - Any notable points or highlights

        Write in a formal, engaging newspaper tone.
        """
    )

    # Initialize the LLMChain with the Llama model and prompt template
    llm_chain = RunnableSequence(
        prompt_template | llm
    )

    # Sample JSON data (replace with your actual JSON data)
    json_data = box_scores_json

    # Generate the newspaper-like summary
    result = llm_chain.invoke(input=json_data)

    # return the result
    return result.content

# Generate Power Rankings
rankings = gen_power_rankings()

# Generate Expected Standings

# Generate Playoff Probability (if week 5 or later) and append to expected standings

# Generate Luck Index

# Generate AI Summary
summary = gen_ai_summary()

# Genrate Power Rankings

# Generate Expected Standings

# Generate Playoff Probability (if week 5 or later) and append to expected standings

# Generate Luck Index
def weeklyLuckIndex(self, teamId, week):
    ''' This function returns an index quantifying how 'lucky' a team was in a given week '''
    team = self.teams[teamId]
    opp = team.schedule[week]

    # Luck Index based on where the team and its opponent finished compared to the rest of the league
    result = team.weeklyResult(week)
    place = self.weeklyFinish(teamId, week)
    if result == 1:  # If the team won...
        odds = (place - 1) / (self.numTeams - 2)  # Odds of this team playing a team with a higher score than it
        luckIndex = 5 * odds  # The worse the team ranked, the luckier they were to have won
    else:  # if the team lost or tied...
        odds = (self.numTeams - place) / (
                    self.numTeams - 2)  # Odds of this team playing a team with a lower score than it
        luckIndex = -5 * odds  # The better the team ranked, the unluckier they were to have lost or tied
    if result == 0.5:  # If the team tied...
        luckIndex /= 2  # They are only half as unlucky, because tying is not as bad as losing

    # Luck Index based on how the team scored compared to its opponent
    teamScore = team.scores[week]
    avgScore = team.avgPointsFor(week)
    stdevScore = team.stdevPointsFor(week)
    if stdevScore != 0:
        zTeam = (teamScore - avgScore) / stdevScore  # Get z-score of the team's performance
        effect = zTeam / (
                    3 * stdevScore) * 2  # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        luckIndex += (effect / abs(effect)) * min(abs(effect), 2)  # The maximum effect is +/- 2

    oppScore = opp.scores[week]
    avgOpp = opp.avgPointsAllowed(week)
    stdevOpp = opp.stdevPointsAllowed(week)
    if stdevOpp != 0:
        zOpp = (oppScore - avgOpp) / stdevOpp  # Get z-score of the opponent's performance
        effect = zOpp / (
                    3 * stdevOpp) * 2  # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        luckIndex -= (effect / abs(effect)) * min(abs(effect), 2)  # The maximum effect is +/- 2

    return luckIndex


def seasonLuckIndex(self, teamId, week):
    ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    luckIndex = 0
    for week in range(1, week + 1):
        luckIndex += self.weeklyLuckIndex(teamId, week)
    return luckIndex


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

print('\n##Summary:\n')
print(summary)
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
