'''
TODO:
1. Injury/bye factor within luck_index.py
2. get_best_lineup() {analytic_utils.py)
'''
from langchain_core.runnables import RunnableSequence

import pandas as pd
from tabulate import tabulate as table
import sys
import argparse
from espn_api.football import League
from datetime import datetime
import re
import json
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from doritostats import luck_index
import time
import progressbar

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

# Create list of teams
teams = league.teams

def gen_power_rankings():
    power_rankings = league.power_rankings(week=week)

    # Extract team names
    extracted_team_names = [(record, re.sub(r'Team\((.*?)\)', r'\1', str(team))) #convert team object to string
        for record, team in power_rankings]

    # Convert to Dataframe
    power_rankings = pd.DataFrame(extracted_team_names, columns=['Power Score','Team'])


    # Switch Score and Team Name cols
    power_rankings_df = power_rankings.reindex(columns=['Team', 'Power Score'])

    if week > 1:
        # Generate last weeks' power rankings for comparison
        prev_power_rankings = league.power_rankings(week=week-1)

        # Extract team names
        extracted_team_names = [(record, re.sub(r'Team\((.*?)\)', r'\1', str(team)))  # convert team object to string
                                for record, team in prev_power_rankings]

        # Convert to Dataframe
        prev_power_rankings_df = pd.DataFrame(extracted_team_names, columns=['Power Score', 'Team'])

        # Switch Score and Team Name cols
        prev_power_rankings_df = prev_power_rankings_df.reindex(columns=['Team', 'Power Score'])

        diffs = []
        emojis = []

        print('This week: \n', power_rankings_df)
        print('Last week: \n', prev_power_rankings_df)

        for team in league.teams:
            # print(team)
            tw_rank = power_rankings_df[power_rankings_df['Team'] == team.team_name].index.values  # get this week's rank
            # print(f'{team.team_name} rank this week: {tw_rank}')
            lw_rank = prev_power_rankings_df[prev_power_rankings_df['Team'] == team.team_name].index.values  # get last weeks' rank
            # print(f'{team.team_name} rank last week: {lw_rank}')
            diff = lw_rank - tw_rank  # find the difference between last week to this week
            # print(f'{team.team_name} weekly change: {diff}')
            diff = int(diff.item())  # turn into list to iterate over
            diffs.append(diff)  # append to the list

        # iterate over diffs list and edit values to include up/down arrow emoji and the number of spots the team moved
        for item in diffs:
            if item > 0:
                emojis.append("**<span style=\"color: green;\">⬆️ " + str(abs(item)) + " </span>**")
            elif item < 0:
                emojis.append("**<span style=\"color: red;\">⬇️ " + str(abs(item)) + " </span>**")
            elif item == 0:
                emojis.append("")  # adds a index of nothing for teams that didn't move

        power_rankings_df.insert(loc=1, column='Weekly Change', value=emojis)  # insert the weekly change column

    return power_rankings_df

def gen_ai_summary():
    print("\nRetrieving and processing matchups...")

    # Retrieve all matchups for the given week
    matchups = league.box_scores(week=week)

    # Create AI summary progress bar
    bar_matchups = progressbar.ProgressBar(max_value=len(matchups))

    # Extract box score data
    box_scores_data = []

    for i, matchup in enumerate(matchups):
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

        # Update progress bar for each matchup processed
        bar_matchups.update(i + 1)

    # Convert to JSON format
    box_scores_json = json.dumps(box_scores_data, indent=4)

    print("\nGenerating summary with LLM...")


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

    # Simulate LLM progress with progress bar
    bar_llm = progressbar.ProgressBar(max_value=1)

    # Generate the newspaper-like summary
    result = llm_chain.invoke(input=box_scores_json)

    # Simulate LLM generation time
    time.sleep(2)
    bar_llm.update(1)

    # return the result
    return result.content

# Generate Power Rankings
rankings = gen_power_rankings()

# Generate Expected Standings

# Generate Playoff Probability (if week 5 or later) and append to expected standings

# Generate Luck Index
print('\nGenerating Luck Index...')
bar_luck_index = progressbar.ProgressBar(max_value=len(teams))

season_luck_index = []
luck_index_value = 0
for i, team in enumerate(teams):
    team_name = team.team_name
    for luck_week in range(1, week+1):
        luck_index_value += luck_index.get_weekly_luck_index(league, team, luck_week)

    # append team's season long luck index to the list
    season_luck_index.append([team, luck_index_value])

    # reset luck index value
    luck_index_value = 0

    # Update the progress bar
    bar_luck_index.update(i + 1)

# convert season long luck index list to pandas dataframe
season_luck_index = pd.DataFrame(season_luck_index, columns=['Team','Luck Index'])

# Generate AI Summary
print('\n\nGenerating AI Summary...')
summary = gen_ai_summary()

# Print everything
print('\nWriting to markdown file...')
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

print('\n## Summary:\n')
print(summary)

# print("\n# EXPECTED STANDINGS (as of week ", week, ")")
# league.printExpectedStandings(week)
# print(table(projectedStandings_prnt, headers='keys', tablefmt='pipe', numalign='center'))

# if week >= 5:
#     print("\n# PLAYOFF PROBABILITIES (as of week ", week, ")")
#     print(table(projections, headers='keys', tablefmt='pipe', numalign='center'))

print("\n## LUCK INDEX")
print(table(season_luck_index, headers='keys', tablefmt='pipe', numalign='center'))

# print("\n WEEK ", week, " ALL PLAY STANDINGS (SORT BY WINS)")
# print(table(allplay, headers='keys', tablefmt='github', numalign='decimal'))

# print("\n WEEK ", week, " POWER SCORE (CALC W/ LEAGUE AVERAGE SCORE)")
# print(table(team_scores_prt, headers='keys', tablefmt='github', numalign='decimal'))

# close text file
sys.stdout.close()
