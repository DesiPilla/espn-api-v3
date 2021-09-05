import json
import requests


year = 2021
league_id = 1086064
endpoint = 'http://fantasy.espn.com/apis/v3/games/ffl/seasons/{}/segments/0/leagues/{}?view=mMatchupScore&view=mTeam&view=mSettings'.format(year, league_id)
requests.get(endpoint)