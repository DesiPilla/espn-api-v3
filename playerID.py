from league import League
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
