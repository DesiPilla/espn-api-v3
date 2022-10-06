import requests
import pandas as pd
from espn_api.football import League

''' FETCH LEAGUE '''
def set_league_endpoint(league: League):
    # (dt.datetime.now() - dt.timedelta(540)).year):         # ESPN API v3
    if (league.year >= (pd.datetime.today() - pd.DateOffset(months=1)).year):
        league.endpoint = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(league.year) + "/segments/0/leagues/" + \
            str(league.league_id) + "?"
    else:                           # ESPN API v2
        league.endpoint = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league.league_id) + "?seasonId=" + str(league.year) + '&'


def get_roster_settings(league: League):
    ''' This grabs the roster and starting lineup settings for the league
            - Grabs the dictionary containing the number of players of each position a roster contains
            - Creates a dictionary rosterSlots{} that only inlcludes slotIds that have a non-zero number of players on the roster
            - Creates a dictionary startingRosterSlots{} that is a subset of rosterSlots{} and only includes slotIds that are on the starting roster
            - Add rosterSlots{} and startingRosterSlots{} to the League attribute League.rosterSettings
    '''
    print('[BUILDING LEAGUE] Gathering roster settings information...')

    # This dictionary maps each slotId to the position it represents
    rosterMap = {0: 'QB', 1: 'TQB', 2: 'RB', 3: 'RB/WR', 4: 'WR',
                 5: 'WR/TE', 6: 'TE', 7: 'OP', 8: 'DT', 9: 'DE',
                 10: 'LB', 11: 'DL', 12: 'CB', 13: 'S', 14: 'DB',
                 15: 'DP', 16: 'D/ST', 17: 'K', 18: 'P', 19: 'HC',
                 20: 'BE', 21: 'IR', 22: '', 23: 'RB/WR/TE', 24: ' '
                 }

    endpoint = '{}view=mMatchupScore&view=mTeam&view=mSettings'.format(
        league.endpoint)
    r = requests.get(endpoint, cookies=league.cookies).json()
    if type(r) == list:
        r = r[0]
    settings = r['settings']
    league.name = settings['name']

    # Grab the dictionary containing the number of players of each position a roster contains
    roster = settings['rosterSettings']['lineupSlotCounts']
    # Create an empty dictionary that will replace roster{}
    rosterSlots = {}
    # Create an empty dictionary that will be a subset of rosterSlots{} containing only starting players
    startingRosterSlots = {}
    for positionId in roster:
        position = rosterMap[int(positionId)]
        # Only inlclude slotIds that have a non-zero number of players on the roster
        if roster[positionId] != 0:
            rosterSlots[position] = roster[positionId]
            # Include all slotIds in the startingRosterSlots{} unless they are bench, injured reserve, or ' '
            if positionId not in ['20', '21', '24']:
                startingRosterSlots[position] = roster[positionId]
    # Add rosterSlots{} and startingRosterSlots{} as a league attribute
    league.roster_settings = {'roster_slots': rosterSlots,
                              'starting_roster_slots': startingRosterSlots}
    return


def fetch_league(league_id: int, year: int, swid: str, espn_s2: str):
    print('[BUILDING LEAGUE] Fetching league data...')
    league = League(league_id=league_id,
                    year=year,
                    swid=swid,
                    espn_s2=espn_s2)

    # Set cookies
    league.cookies = {'swid': swid, 'espn_s2': espn_s2}

    # Set league endpoint
    set_league_endpoint(league)

    # Get roster information
    get_roster_settings(league)

    # Load current league data
    print('[BUILDING LEAGUE] Loading current league details...')
    league.load_roster_week(league.current_week)
    return league


