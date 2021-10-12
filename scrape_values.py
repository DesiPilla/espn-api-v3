from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from progressbar import ProgressBar
from tqdm import tqdm
from tabulate import tabulate as table

pbar = ProgressBar()

def player_values(week):
    root = '/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/values/week'

    url = 'https://www.fantasysp.com/trade-value-chart/nfl'

    # this is the HTML from the given URL
    html = urlopen(url)

    soup = BeautifulSoup(html, features='lxml') #features ensures runs the same on different systems

    # use findALL() to get the column headers
    soup.findAll('tr', limit=2)

    # use getText()to extract the text we need into a list
    headers = [th.getText() for th in soup.findAll('tr', limit=2)[1].findAll('th')]
    # exclude the first column

    # headers = headers[1:]

    # print(headers)

    # if its the first year, create blank dataframe, need to do here to get headers


    # avoid the first header row
    rows = soup.findAll('tr')[1:]
    team_stats = [[td.getText() for td in rows[i].findAll('td')]
            for i in range(len(rows))]

    # save as pandas dataframe
    stats = pd.DataFrame(team_stats, columns=headers)

    # drop rows that aren't part of the ratings
    stats = stats.dropna(axis=0)

    # remove positions
    stats['Player'] = stats['Player'].replace(' QB ', '', regex=True)
    stats['Player'] = stats['Player'].replace(' RB ', '', regex=True)
    stats['Player'] = stats['Player'].replace(' WR ', '', regex=True)
    stats['Player'] = stats['Player'].replace(' TE ', '', regex=True)
    stats['Player'] = stats['Player'].replace(' K ', '', regex=True)

    # change vs last week column headers
    stats.rename(columns={'vs LAST WEEK':'change'}, inplace=True)

    # subset columns that we need
    stats = stats[['Player','RATING','change']]

    return stats
