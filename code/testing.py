import json
import requests
import pandas as pd

from espn_api.football import League, Team, Player


year = 2021
league_id = 1086064

login = pd.read_csv('login.csv')
manager, league_name, league_id, swid, espn_s2 = login.iloc[0]

endpoint = 'http://fantasy.espn.com/apis/v3/games/ffl/seasons/{}/segments/0/leagues/{}?view=mMatchupScore&view=mTeam&view=mSettings'.format(year, league_id)  
cookies={'SWID': swid, "espn_s2": espn_s2}
a = requests.get(endpoint, cookies=cookies).json()



league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
league.cookies = {'swid':swid, 'espn_s2':espn_s2}


getRosterSettings(league)