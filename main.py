from league import League
from authorize import Authorize
from team import Team
from player import Player

import requests
from tabulate import tabulate as table

username = 'email@gmail.com'
password = 'password';
league_id = 1086064
year = 2019

league = League(league_id, 2019, username, password)
print(league)
