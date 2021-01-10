import requests
import datetime

# Import the Team class (this is complicated because team.py is in the parent folder)
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from team import Team

''' 
***********************************************************
*   League fetching/building methods for League class     *
***********************************************************
'''  

def buildLeague(league):
    # ESPN Fantasy Football API v3 came out for seasons in 2019 and beyond. v2 is used up until 2018
    print('[BUILDING LEAGUE] Fetching league...')
    if (league.year >= (datetime.datetime.now() - datetime.timedelta(180)).year):         # ESPN API v3
        league.url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(league.year) + "/segments/0/leagues/" + str(league.league_id)
    else:                           # ESPN API v2
        league.url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league.league_id) + "?seasonId=" + str(league.year)
    
    league.cookies = {'swid' : league.swid, 'espn_s2' : league.espn_s2}
    settings = requests.get(league.url, cookies = league.cookies, params = {'view' : 'mSettings'}).json()
    
    # Try navigating the settings tree. If an error occurs, the league is not accessible
    try:
        if league.year >= 2019:
            league.currentWeek = settings['scoringPeriodId']
            league.settings = settings['settings']
        else:
            league.currentWeek = settings[0]['scoringPeriodId']
            league.settings = settings[0]['settings']
        print('[BUILDING LEAGUE] League authenticated!')
    except:
        raise Exception('[BUILDING LEAGUE] ERROR: League is not accessible: swid and espn_s2 needed.')
    
    # Gather league information
    print('[BUILDING LEAGUE] Gathering team information...')
    league.regSeasonWeeks = league.settings['scheduleSettings']['matchupPeriodCount']
    league.teamData = requests.get(league.url, cookies = league.cookies, params = {'view' : 'mTeam'}).json()
    print('[BUILDING LEAGUE] Gathering matchup data...')
    league.matchupData = requests.get(league.url, cookies = league.cookies, params = {'view' : 'mMatchupScore'}).json()
    if league.year < 2019:
        league.teamData = league.teamData[0]
        league.matchupData = league.matchupData[0]
            
    # Build league
    getTeamNames(league) 
    getRosterSettings(league) 
    buildTeams(league)
    #getWeeklyProjections(league)
    print('[BUILDING LEAGUE] League successfully built!')    
    return

def getRosterSettings(league):
    ''' This grabs the roster and starting lineup settings for the league
            - Grabs the dictionary containing the number of players of each position a roster contains
            - Creates a dictionary rosterSlots{} that only inlcludes slotIds that have a non-zero number of players on the roster
            - Creates a dictionary startingRosterSlots{} that is a subset of rosterSlots{} and only includes slotIds that are on the starting roster
            - Add rosterSlots{} and startingRosterSlots{} to the League attribute League.rosterSettings
    '''
    print('[BUILDING LEAGUE] Gathering roster settings information...')
    
    # This dictionary maps each slotId to the position it represents
    league.rosterMap = { 0 : 'QB', 1 : 'TQB', 2 : 'RB', 3 : 'RB/WR', 4 : 'WR',
                       5 : 'WR/TE', 6 : 'TE', 7 : 'OP', 8 : 'DT', 9 : 'DE',
                       10 : 'LB', 11 : 'DL', 12 : 'CB', 13 : 'S', 14 : 'DB',
                       15 : 'DP', 16 : 'D/ST', 17 : 'K', 18 : 'P', 19 : 'HC',
                       20 : 'BE', 21 : 'IR', 22 : '', 23 : 'RB/WR/TE', 24 : ' '
                       }
    
    roster = league.settings['rosterSettings']['lineupSlotCounts']    # Grab the dictionary containing the number of players of each position a roster contains
    rosterSlots = {}                                                # Create an empty dictionary that will replace roster{}
    startingRosterSlots = {}                                        # Create an empty dictionary that will be a subset of rosterSlots{} containing only starting players
    for positionId in roster:
        if roster[positionId] != 0:                                 # Only inlclude slotIds that have a non-zero number of players on the roster
            rosterSlots[positionId] = roster[positionId]
            if positionId not in ['20', '21', '24']:              # Include all slotIds in the startingRosterSlots{} unless they are bench, injured reserve, or ' '
                startingRosterSlots[positionId] = [roster[positionId], league.rosterMap[int(positionId)]]
    league.rosterSettings = {'rosterSlots' : rosterSlots, 'startingRosterSlots' : startingRosterSlots}    # Add rosterSlots{} and startingRosterSlots{} as a league attribute
    return  

def getTeamNames(league):
    """ This function takes the teamData of a league and:
            - Finds the number of teams in the league
            - Creates a dictionary league.swids where the user SWID is the key and the user's full name is the value
            - Creates a dictionary league.teamNames where the teamIndex is the key and a list containing [ownerName, teamName] is the value
    """
    league.numTeams = len(league.teamData['teams'])          # Find the number of teams in the league
    
    league.swids = {}                                      # Create an empty swids dictionary
    for member in league.teamData['members']:              # Add each swid and ownerName to the swids dictionary
        league.swids[member['id']] = '%s %s' % (member['firstName'], member['lastName'])
    
    league.teamNames = {}                                  # Create an empty teamNames dictionary
    league.adjustIds= {}
    id = 1
    for team in league.teamData['teams']:
        if team['id'] != id:                                    # If the teamId is not what it is supposed to be...
            league.adjustIds[team['id']] = id                     # Save the incorrect teamId for future reference
            league.teamData['teams'][id - 1]['id'] = id           # Correct the teamId of the copied team
        else: 
            league.adjustIds[id] = id
        id += 1
    
    id = 1        
    for team in league.teamData['teams']:
        teamId = team['id']                                     # Get the teamId of each team
        name = '%s %s' % (team['location'], team['nickname'])   # Get the name of each team
        swid = team['primaryOwner']                             # Get the swid of each team
        owner = league.swids[swid]                                # Get the owner's name for each team
        league.teamNames[teamId] = owner                          # Populate the teamNames dictionary
        id += 1
    return

def buildTeams(league):
    """ This function builds the Team objects for each team in the league """
    league.teams = {}                                                             # Create an empty teams dictionary
    matchupData = league.matchupData
    print("[BUILDING LEAGUE] Current Week:",league.currentWeek)
    print('[BUILDING LEAGUE] Building teams...')
    for teamId in range(1, league.numTeams + 1):
        team = Team(league.teamData['teams'][teamId-1])                           # Create a Team object for each team in the league
        team.nameOwner(league.teamNames[teamId])                                  # Name the team owner
        team.startingRosterSlots = league.rosterSettings['startingRosterSlots']   # Define the league startingRosterSlots setting for each team
        league.teams[teamId] = team                                               # Add each Team object to the teams dictionary
    
    print('[BUILDING LEAGUE] Building schedule...')
    numMatchups = (league.currentWeek - 1)*league.numTeams // 2     # Determines the number of matchups that have been completed (not including the current week)
    for week in range(1, league.settings['scheduleSettings']['matchupPeriodCount'] + 1):
        # Build the matchups for every week
        if week < league.currentWeek:
            matchupData = requests.get(league.url, cookies = league.cookies, params = { 'view' : 'mMatchupScore', 'view' : 'mMatchup', 'scoringPeriodId': week }).json()
            if league.year < 2019:
                matchupData = matchupData[0]
        else: 
            matchupData = league.matchupData
        
        
        print('[BUILDING LEAGUE] \tBuilding week %d/%d...' % (week, league.settings['scheduleSettings']['matchupPeriodCount']))             
        for m in range((week-1)*league.numTeams // 2, (week)*league.numTeams // 2):  
            awayTeam = matchupData['schedule'][m]['away']           # Define the away team of the matchup
            homeTeam = matchupData['schedule'][m]['home']           # Define the home team of the matchup
            
            awayId = league.adjustIds[awayTeam['teamId']]             # Define the teamIndex of the away team
            homeId = league.adjustIds[homeTeam['teamId']]             # Define the teamIndex of the home team
            
            league.teams[awayId].schedule[week] = league.teams[homeId]  # Add this matchup to the schedule of the away team's Team object
            league.teams[homeId].schedule[week] = league.teams[awayId]  # Add this matchup to the schedule of the home team's Team object
            
            if league.year >= 2019:
                if m < numMatchups:
                    league.teams[awayId].addMatchup(awayTeam, week, league.year)       # Add this matchup to the away team's Team object
                    league.teams[homeId].addMatchup(homeTeam, week, league.year)       # Add this matchup to the home team's Team object   
            else:
                if m < numMatchups:
                    rosterData = requests.get(league.url, cookies = league.cookies, params = {'view' : 'mRoster', 'scoringPeriodId': week}).json()[0]
                    league.teams[awayId].addMatchup(rosterData['teams'][awayId - 1]['roster']['entries'], week, league.year)
                    league.teams[homeId].addMatchup(rosterData['teams'][homeId - 1]['roster']['entries'], week, league.year)
                    
        week += 1         
        
    return
        
def loadWeeklyRosters(league, week):
    '''Sets Teams Roster for a Certain Week'''
    params = {'view': 'mRoster', 'scoringPeriodId': week}       # Specify the request parameters for the given week
    rosterData = requests.get(league.url, params = params, cookies = league.cookies).json() # Fetch roster data for the given week
    if league.year < 2019:
        rosterData = rosterData[0]                              # Adjust rosterData for ESPN API v2
    for teamId in league.teams:                                   # Fetch the roster of each team for the given week                 
        league.teams[teamId].fetchWeeklyRoster(rosterData['teams'][league.teams[teamId].teamId - 1]['roster'], week)
    return  


def getWeeklyProjections(league):
    # NOT WORKING
    for week in range(1, league.currentWeek):
        data = requests.get(league.url, cookies = league.cookies, params = {'scoringPeriodId': week}).json()
        for team in data['teams']:
            teamData = team['roster']['entries']
            i = 0
            for player in team.rosters[week]:
                player.projection = teamData[i]['playerPoolEntry']['player']['stats'][1]['appliedTotal']
                player.testName = teamData[i]['playerPoolEntry']['player']['fullName']
                i += 1
    return


def getUrl(year, league_id):
    '''
    Define endpoint for accessing the ESPN API.
    For seasons that started in 2018 and earlier, use the ESPN v2 endpoint.
    For seasons that started in 2019 and later, use the ESPN v3 endpoint.
    '''
    url = ''
    if (year >= 2019):         # ESPN API v3
        url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(year) + "/segments/0/leagues/" + str(league_id)
    else:                      # ESPN API v2
        url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league_id) + "?seasonId=" + str(year)
    return url