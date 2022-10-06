import pandas as pd

from fetch_utils import (
    fetch_league
)

year = 2022
login = pd.read_csv('login.csv')
manager, league_name, league_id, swid, espn_s2 = login.iloc[0]

def test1():
    league = fetch_league(league_id=league_id,
                        year=year,
                        swid=swid, 
                        espn_s2=espn_s2)
    print('pass')
    return


if __name__ == '__main__':
    test1()