from urllib.request import urlopen
from bs4 import BeautifulSoup
import pandas as pd
from progressbar import ProgressBar
from tqdm import tqdm
from tabulate import tabulate as table

pbar = ProgressBar()

root = '/Users/christiangeer/Fantasy_Sports/football/power_rankings/espn-api-v3/values/week'

positions = ['QB','RB','WR','TE']

def player_values(week):
    for pos in positions:
        url = 'https://www.fantasysp.com/trade-value-chart/nfl/{}'.format(pos)

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

        # if its the first pos (qb), create blank dataframe, need to do here to get headers
        if pos == 'QB':
            all_pos = pd.DataFrame(columns=headers)

        # avoid the first header row
        rows = soup.findAll('tr')[1:]
        team_stats = [[td.getText() for td in rows[i].findAll('td')]
                for i in range(len(rows))]

        # save as pandas dataframe
        stats = pd.DataFrame(team_stats, columns=headers)
        stats['position'] = pos

        # apppend to datafraem
        all_pos = all_pos.append(stats)


    # drop rows that aren't part of the ratings (na ratings)
    all_pos = all_pos[all_pos['RATING'].notna()]

    # remove positions
    all_pos['Player'] = all_pos['Player'].replace(' $', '', regex=True)


    # change vs last week column headers
    all_pos.rename(columns={'vs LAST WEEK':'change'}, inplace=True)

    # subset columns that we need
    all_pos = all_pos[['Player','RATING','position']]

    return all_pos
