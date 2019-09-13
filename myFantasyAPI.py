import requests
from tabulate import tabulate as table



# FOR 2018 AND BEFORE
if False:
    year = 2018
    url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
          str(league_id) + "?seasonId=" + str(year)
    r = requests.get(url)
    d = r.json()[0]



''' 
To get the SWID and s2 for the league, sign into your league in chrome. 
Then, press CTRL + SHIFT + C to open the DevTools extension.
Scroll over to Application and open that tab.
Under Storage, open cookies.
There, you will find the espnAuth and espn_s2 cookies cached in the browser.
'''

# See a docstring by typing >> instance.function.__doc__

class League():
    
    def __init__(self, league_id, year, swid = None, espn_s2 = None):
        self.league_id = league_id
        self.year = year
        self.swid = swid
        self.espn_s2 = espn_s2

        # ESPN Fantasy Football API v3 came out for seasons in 2019 and beyond. v2 is used up until 2018
        print('Fetching league...')
        if (self.year >= 2019):         # ESPN API v3
            self.url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
                str(self.year) + "/segments/0/leagues/" + str(self.league_id)
        else:                           # ESPN API v2
            self.url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
                str(self.league_id) + "?seasonId=" + str(self.year)
        
        self.cookies = {'swid' : self.swid, 'espn_s2' : self.espn_s2};
        settings = requests.get(self.url, cookies = self.cookies, params = {'view' : 'mSettings'}).json()
        
        # Try navigating the settings tree. If an error occurs, the league is not accessible
        try:
            if self.year >= 2019:
                self.currentWeek = settings['scoringPeriodId']
                self.settings = settings['settings']
            else:
                self.currentWeek = settings[0]['scoringPeriodId']
                self.settings = settings[0]['settings']
            print('League authenticated!')
        except:
            raise Exception('ERROR: League is not accessible: swid and espn_s2 needed.')
        
        # Gather league information
        print('Gathering team information...')
        self.regSeasonWeeks = self.settings['scheduleSettings']['matchupPeriodCount']
        self.teamData = requests.get(self.url, cookies = self.cookies, params = {'view' : 'mTeam'}).json()
        print('Gathering matchup data...')
        self.matchupData = requests.get(self.url, cookies = self.cookies, params = {'view' : 'mMatchup'}).json()
        if year < 2019:
            self.teamData = self.teamData[0]
            self.matchupData = self.matchupData[0]        
                
        # Build league
        self.getTeamNames() 
        self.getRosterSettings() 
        print(self.teamNames)  
        self.buildTeams()
        print('League successfully built!')
        
        return
        
        
    def __repr__(self):
        """This is what is displayed when print(league) is entered """
        return 'League(%s, %s)' % (self.settings['name'], self.year, ) 
    
    def getRosterSettings(self):
        ''' This grabs the roster and starting lineup settings for the league
                - Grabs the dictionary containing the number of players of each position a roster contains
                - Creates a dictionary rosterSlots{} that only inlcludes slotIds that have a non-zero number of players on the roster
                - Creates a dictionary startingRosterSlots{} that is a subset of rosterSlots{} and only includes slotIds that are on the starting roster
                - Add rosterSlots{} and startingRosterSlots{} to the League attribute League.rosterSettings
        '''
        print('Gathering roster settings information...')
        
        # This dictionary maps each slotId to the position it represents
        self.rosterMap = { 0 : 'QB', 1 : 'TQB', 2 : 'RB', 3 : 'RB/WR', 4 : 'WR',
                           5 : 'WR/TE', 6 : 'TE', 7 : 'OP', 8 : 'DT', 9 : 'DE',
                           10 : 'LB', 11 : 'DL', 12 : 'CB', 13 : 'S', 14 : 'DB',
                           15 : 'DP', 16 : 'D/ST', 17 : 'K', 18 : 'P', 19 : 'HC',
                           20 : 'BE', 21 : 'IR', 22 : '', 23 : 'RB/WR/TE', 24 : ' '
                           }
        
        roster = self.settings['rosterSettings']['lineupSlotCounts']    # Grab the dictionary containing the number of players of each position a roster contains
        rosterSlots = {}                                                # Create an empty dictionary that will replace roster{}
        startingRosterSlots = {}                                        # Create an empty dictionary that will be a subset of rosterSlots{} containing only starting players
        for positionId in roster:
            if roster[positionId] != 0:                                 # Only inlclude slotIds that have a non-zero number of players on the roster
                rosterSlots[positionId] = roster[positionId]
                if positionId not in ['20', '21', '24']:              # Include all slotIds in the startingRosterSlots{} unless they are bench, injured reserve, or ' '
                    startingRosterSlots[positionId] = [roster[positionId], self.rosterMap[int(positionId)]]
        self.rosterSettings = {'rosterSlots' : rosterSlots, 'startingRosterSlots' : startingRosterSlots}    # Add rosterSlots{} and startingRosterSlots{} as a league attribute
        return
    
    def getTeamNames(self):
        """ This function takes the teamData of a league and:
                - Finds the number of teams in the league
                - Creates a dictionary self.swids where the user SWID is the key and the user's full name is the value
                - Creates a dictionary self.teamNames where the teamIndex is the key and a list containing [ownerName, teamName] is the value
        """
        self.numTeams = len(self.teamData['teams'])          # Find the number of teams in the league
        
        self.swids = {}                                      # Create an empty swids dictionary
        for member in self.teamData['members']:              # Add each swid and ownerName to the swids dictionary
            self.swids[member['id']] = '%s %s' % (member['firstName'], member['lastName'])
        
        self.teamNames = {}                                  # Create an empty teamNames dictionary
        id = 1
        for team in self.teamData['teams']:
            teamId = id
            teamId = team['id']                                     # Get the teamId of each team
            name = '%s %s' % (team['location'], team['nickname'])   # Get the name of each team
            swid = team['primaryOwner']                             # Get the swid of each team
            owner = self.swids[swid]                                # Get the owner's name for each team
            self.teamNames[teamId] = [owner, name]                  # Populate the teamNames dictionary
            id += 1
        return
    
    def buildTeams(self):
        """ This function builds the Team objects for each team in the league """
        self.teams = {}                                                             # Create an empty teams dictionary
        matchupData = self.matchupData
        print("Current Week:",self.currentWeek)
        print('Building teams...')
        for teamId in range(1, self.numTeams + 1):
            team = Team(self.teamData['teams'][teamId-1])                           # Create a Team object for each team in the league
            team.nameOwner(self.teamNames[teamId])                                  # Name the team owner
            team.startingRosterSlots = self.rosterSettings['startingRosterSlots']   # Define the league startingRosterSlots setting for each team
            self.teams[teamId] = team                                               # Add each Team object to the teams dictionary
        
        
        print('Building schedule...')
        numMatchups = (self.currentWeek - 1)*self.numTeams // 2     # Determines the number of matchups that have been completed (not including the current week)
        for week in range(self.settings['scheduleSettings']['matchupPeriodCount']):
            # Build the matchups for every week
            week += 1
            print('\tBuilding week %d/%d...' % (week, self.settings['scheduleSettings']['matchupPeriodCount']))             
            for m in range((week-1)*self.numTeams // 2, (week)*self.numTeams // 2):  
                awayTeam = matchupData['schedule'][m]['away']           # Define the away team of the matchup
                homeTeam = matchupData['schedule'][m]['home']           # Define the home team of the matchup
                awayId = awayTeam['teamId']                             # Define the teamIndex of the away team
                homeId = homeTeam['teamId']                             # Define the teamIndex of the home team
                self.teams[awayId].schedule[week] = self.teams[homeId]  # Add this matchup to the schedule of the away team's Team object
                self.teams[homeId].schedule[week] = self.teams[awayId]  # Add this matchup to the schedule of the home team's Team object
                if m < numMatchups:
                    self.teams[awayId].addMatchup(awayTeam, week)       # Add this matchup to the away team's Team object
                    self.teams[homeId].addMatchup(homeTeam, week)       # Add this matchup to the home team's Team object            
                
            if week < self.currentWeek:
                self.loadWeeklyRosters(week)                        # Add the roster data for weeks that have already concluded
                
        return
        
    def loadWeeklyRosters(self, week):
        '''Sets Teams Roster for a Certain Week'''
        params = {'view': 'mRoster', 'scoringPeriodId': week}       # Specify the request parameters for the given week
        rosterData = requests.get(self.url, params = params, cookies = self.cookies).json() # Fetch roster data for the given week
        if self.year < 2019:
            rosterData = rosterData[0]                              # Adjust rosterData for ESPN API v2
        for teamId in self.teams:                                   # Fetch the roster of each team for the given week                 
            self.teams[teamId].fetchWeeklyRoster(rosterData['teams'][self.teams[teamId].teamId - 1]['roster'], week)
        return
    
    
    ''' **************************************************
        *         Begin advanced stats methods           *
        ************************************************** '''
    
    def weeklyScore(self, teamId, week):
        ''' Returns the number of points scored by a team's starting roster for a given week. '''
        if week <= self.currentWeek:
            return self.teams[teamId].scores[week]
        else:
            return None
        
    def printWeeklyScores(self, teamId):
        ''' Prints all weekly scores for a given team. '''
        print('  ---',self.teams[teamId].teamName,'---')
        for week in range(1, self.currentWeek):
            score = self.weeklyScore(teamId, week)
            print('Week ', week, ': ', round(score, 1))
        sum = 0
        for i in range(1, self.currentWeek):
            sum += self.teams[teamId].scores[i]
        avg = sum/ (self.currentWeek - 1)
        print('-------------------------------','\nAvg. Score:', '%.2f' % avg)
        return
        
    def topPlayers(self, teamId, week, slotCategoryId, n):
        ''' Takes a list of players and returns a list of the top n players based on points scored. '''
        # Gather players of the desired position
        unsortedList = []
        for player in self.teams[teamId].rosters[week]:
            if slotCategoryId in player.eligibleSlots:
                unsortedList += [player]
                
        # Sort players by points scored
        sortedList = [unsortedList[0]]
        for player in unsortedList[1:]:
            for i in range(len(sortedList)):
                if (player.score >= sortedList[i].score):
                    sortedList = sortedList[:i] + [player] + sortedList[i:]
                    break
            if player not in sortedList:
                sortedList += [player]
        return sortedList[:n]
       
    def printWeeklyMatchResults(self, teamId):
        ''' Prints all weekly match results for a given team. '''
        team = self.teams[teamId]
        print('  ---',team.teamName,'---')
        for week in range(1, leg.currentWeek):
            print('Week',str(week+1),': ', end ="")
            print('%.2f' % team.scores[week], '-', '%.2f' % team.schedule[week].scores[week], end='')
            print('   vs.', team.schedule[week].owner[0])
        print('------------------------------------------------------------')
        print('Season Record:',str(team.wins),'-',str(team.losses),'-',str(team.ties)) 
    
    def bestTrio(self, teamId, week):
        ''' Returns the the sum of the top QB/RB/Reciever trio for a team during a given week. '''
        qb = self.topPlayers(teamId, week, 0, 1)[0].score
        rb = self.topPlayers(teamId, week, 2, 1)[0].score
        wr = self.topPlayers(teamId, week, 4, 1)[0].score
        te = self.topPlayers(teamId, week, 6, 1)[0].score
        bestTrio = round(qb + rb + max(wr, te), 2)
        return bestTrio  
    
    # Returns the rank of a team based on the weekly score of a team for a given week.
    def weeklyFinish(self, teamId, week):
        team = self.teams[teamId]                           # Get the Team object associated with the input teamId
        teamIds = list(range(1, self.numTeams + 1))         # Get a list of teamIds 
        teamIds.remove(team.teamId)                       # Remove the teamId of the working team from the list of teamIds
        weeklyFinish = 1                                    # Initialize the weeklyFinish to 1
        for teamId in teamIds:
            if (team.scores[week] != self.teams[teamId].scores[week]) and (team.scores[week] <= self.teams[teamId].scores[week]):
                weeklyFinish += 1;                          # Increment the weeklyFinish for every team with a higher weekly score
        return weeklyFinish
        

    ''' **************************************************
        *          Begin stat sortitng methods           *
        ************************************************** '''  

    def dictValuesToList(self, dict):
        ''' Takes a dictionary and creates a list containing all values. '''
        list = []
        for value in dict.values():
            list += [value]  
        return list
    
    def listsToDict(self, keys, vals):
        ''' Takes a list of keys and a list of values and creates a dictionary. '''
        dict = {}
        for i in range(len(keys)):
            dict[keys[i]] = vals[i]
        return dict
    
    def sortWeeklyScore(self, week):
        ''' Sorts league teams for a given week based on weekly score (highest score is first). '''
        teams = self.dictValuesToList(self.teams)      
        sortedTeams = sorted(teams, key=lambda x: x.scores[week],
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict
    

    def sortBestLineup(self, week):
        ''' Sorts league teams for a given week based on best possible lineup (highest score is first). '''
        teams = self.dictValuesToList(self.teams)      
        sortedTeams = sorted(teams, key=lambda x: x.bestLineup(week),
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict   

    def sortOpponentScore(self, week):
        ''' Sorts league teams for a given week based on their opponent's score (highest opponent score is first). '''
        teams = self.dictValuesToList(self.teams)      
        sortedTeams = sorted(teams, key=lambda x: x.schedule[week].scores[week],
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict
    
    def sortBestTrio(self, week):
        ''' Sorts league teams for a given week based on their best QB/RB/Receiver trio (highest score is first). '''
        teams = self.dictValuesToList(self.teams)      
        sortedTeams = sorted(teams, key=lambda x: x.bestTrio(week),
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict
    
    def sortNumOut(week):
        ''' Sorts league teams for a given week based on the number of players who did not play (least injuries is first). '''
        teams = self.dictValuesToList(self.teams)      
        sortedTeams = sorted(teams, key=lambda x: x.numOut(week),
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict
    
    def sortPositionScore(self, week, slotId):
        ''' Sorts league teams for a given week based on the average starting slotId points (highest score is first) '''  
        teams = self.dictValuesToList(self.teams)
        sortedTeams = sorted(teams, key=lambda x: x.avgStartingScore(week, slotId),
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict    

    def sortBenchPoints(self, week):
        ''' Sorts league teams for a given week based on the total bench points (highest score is first). '''
        teams = self.dictValuesToList(self.teams)
        sortedTeams = sorted(teams, key=lambda x: x.totalBenchPoints(week),
                              reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict       

    def sortDifference(self, week):
        ''' Sorts league teams for a given week based on the the difference between their 
        best possible score and their actual score (lowest difference is first). '''
        teams = self.dictValuesToList(self.teams)
        sortedTeams = sorted(teams, key=lambda x: x.scores[week] - x.schedule[week].scores[week], reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict      
    
    def sortOverallRoster(self, week):
        ''' Sorts league teams for a given week based on total roster points (highest score is first). '''
        teams = self.dictValuesToList(self.teams)
        sortedTeams = sorted(teams, key=lambda x: (x.totalBenchPoints(week) + x.scores[week]), reverse=True)
        ranks = list(range(1, self.numTeams + 1))
        sortedTeamDict = self.listsToDict(ranks, sortedTeams)
        return sortedTeamDict        
            
    def printWeeklyStats(self, week):
        ''' Prints weekly stat report for a league during a given week. '''
        last = self.numTeams
        stats_table = [['Most Points Scored: ', self.sortWeeklyScore(week)[1].owner[0].split(' ')[0]],
                       ['Least Points Scored: ', self.sortWeeklyScore(week)[last].owner[0].split(' ')[0]],
                       ['Best Possible Lineup: ', self.sortBestLineup(week)[1].owner[0].split(' ')[0]],
                       ['Best Trio: ', self.sortBestTrio(week)[1].owner[0].split(' ')[0]],
                       ['Worst Trio: ', self.sortBestTrio(week)[last].owner[0].split(' ')[0]],
                       
                       ['---------------------','----------------'],
                       ['Best QBs: ', self.sortPositionScore(week, 0)[1].owner[0].split(' ')[0]],
                       ['Best RBs: ', self.sortPositionScore(week, 2)[1].owner[0].split(' ')[0]],
                       ['Best WRs: ', self.sortPositionScore(week, 4)[1].owner[0].split(' ')[0]], 
                       ['Best TEs: ', self.sortPositionScore(week, 6)[1].owner[0].split(' ')[0]],
                       ['Best Flex: ', self.sortPositionScore(week, 23)[1].owner[0].split(' ')[0]],
                       ['Best DST: ', self.sortPositionScore(week, 16)[1].owner[0].split(' ')[0]],
                       ['Best K: ', self.sortPositionScore(week, 17)[1].owner[0].split(' ')[0]],
                       ['Best Bench: ', self.sortBenchPoints(week)[1].owner[0].split(' ')[0]],
                       ['---------------------','----------------'],
                       ['Worst QBs: ', self.sortPositionScore(week, 0)[last].owner[0].split(' ')[0]],
                       ['Worst RBs: ', self.sortPositionScore(week, 2)[last].owner[0].split(' ')[0]],
                       ['Worst WRs: ', self.sortPositionScore(week, 4)[last].owner[0].split(' ')[0]], 
                       ['Worst TEs: ', self.sortPositionScore(week, 6)[last].owner[0].split(' ')[0]],
                       ['Worst Flex: ', self.sortPositionScore(week, 23)[last].owner[0].split(' ')[0]],
                       ['Worst DST: ', self.sortPositionScore(week, 16)[last].owner[0].split(' ')[0]],
                       ['Worst K: ', self.sortPositionScore(week, 17)[last].owner[0].split(' ')[0]],
                       ['Worst Bench: ', self.sortBenchPoints(week)[last].owner[0].split(' ')[0]]]
        print('\n', table(stats_table, headers = ['Week ' + str(week), '']))   
    
        # ['Most Injuries: ', self.sortNumOut(week)[last].owner.split(' ')[0]],
        # ['Least Injuries: ', self.sortNumOut(week)[0].owner.split(' ')[0]],
        return
    
    def teamWeeklyPRank(self, teamId, week):
        ''' Returns the power rank score of a team for a certain week. '''
        team = self.teams[teamId]
        
        # Points for score
        bestWeeklyScore = self.sortWeeklyScore(week)[1].scores[week]
        score = self.weeklyScore(teamId, week)
        pfScore = score / bestWeeklyScore * 70
        
        # Team Record score
        oppScore = team.schedule[week].scores[week]
        if score > oppScore:
            win = 5             # Team won this week
        if score == oppScore:
            win = 2.5           # Team tied this week
        else:
            win = 0             # Team lost this week
        bestScore = team.bestLineup(week)    # Best possible lineup for team
        oppBestScore = team.schedule[week].bestLineup(week)
        if bestScore > oppBestScore:
            luck = 10           # Team should have won if both lineups were their best
        elif bestScore > oppScore:
            luck = 5            # Team could have won if their lineup was its best
        else: 
            luck = 0            # Team could not have won
        multiplier = 1 + (win + luck) / 100
        
        # Best lineup score
        bestBestWeeklyScore = self.sortBestLineup(week)[1].scores[week]
        bestLineupScore = bestScore / bestBestWeeklyScore * 20
        
        # Dominance score
        if score > oppScore:
            dominance = (score - oppScore) / score * 10
        else:
            dominance = 0
        
        #print(team.owner, '\t', round(pfScore,1), '\t', round(pfScore * multiplier,1), '\t', round(bestLineupScore,1), '\t', round(dominance,1))
        
        return pfScore*multiplier + bestLineupScore + dominance
    
    def teamTotalPRank(self, teamId, week):
        ''' Gets overall power ranking for a team. ''' 
        pRank = 0
        for w in range(1, week+1):
            pRank += self.teamWeeklyPRank(teamId, w)
        pRank += self.teamWeeklyPRank(teamId, week)*2
        if week > 1:
            pRank += self.teamWeeklyPRank(teamId, week-1)
            week += 1
        return pRank / (week + 2)
    
    def printMyPowerRankings(self, week):
        ''' Print my power rankings in a nice table. '''
        powerRankings = []
        for teamId in range(1, self.numTeams + 1):
            powerRankings += [[self.teamTotalPRank(teamId, week), self.teams[teamId]]]
        sortedRankings = sorted(powerRankings, key=lambda x: x[0], reverse=True)        
        powerRankingsTable = []
        for team in sortedRankings:
            powerRankingsTable += [[ team[1].teamName,
                                       team[0],
                                       team[1].owner[0] ]]
        print('\n','Week ',week, '\n', table( powerRankingsTable, headers = ['Power Index', 'Team', 'Owner'], floatfmt = '.2f')) 
    
    
    
class Authorize():
    
    def __init__(self, username = None, password = None):
        self.username = username
        self.password = password
        self.swid = None
        self.espn_s2 = None  
        self.authorize()
 
    def authorize(self):
        headers = {'Content-Type': 'application/json'}
        siteInfo = requests.post('https://registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/api-key?langPref=en-US', headers = headers
        )
        if siteInfo.status_code != 200 or 'api-key' not in siteInfo.headers:
            raise AuthorizationError('failed to get API key')        
        api_key = siteInfo.headers['api-key']
        headers['authorization'] = 'APIKEY ' + api_key

        payload = {'loginValue': self.username, 'password': self.password}

        siteInfo = requests.post(
            'https://ha.registerdisney.go.com/jgc/v5/client/ESPN-FANTASYLM-PROD/guest/login?langPref=en-US', headers = headers, json = payload
        )
        
        if siteInfo.status_code != 200:
            raise AuthorizationError('unable to authorize')

        data = siteInfo.json()

        if data['error'] is not None:
            raise AuthorizationError('unable to obtain autorization')

        self.swid = data['data']['profile']['swid'][1:-1]
        self.espn_s2 = data['data']['s2']

    def get_league(self, league_id, year):
        return League(league_id, year, self.espn_s2, self.swid)
        
    
    
class Team():
    """
    teamData['teams'][teamId - 1]
    """
    def __init__(self, teamData):
        self.teamId = teamData['id']
        self.teamAbbrev = teamData['abbrev']
        self.teamName = "%s %s" % (teamData['location'], teamData['nickname'])
        self.divisionId = teamData['divisionId']
        self.wins = teamData['record']['overall']['wins']
        self.losses = teamData['record']['overall']['losses']
        self.ties = teamData['record']['overall']['ties']
        self.pointsFor = teamData['record']['overall']['pointsFor']
        self.pointsAgainst = teamData['record']['overall']['pointsAgainst']
        self.owner = "Unknown"
        
        self.schedule = {}              # Constructed by League.buildTeams
        self.scores = {}                # Constructed by League.buildTeams when it calls Team.addMatchup
        self.rosters = {}               # Constructed by League.buildTeams when it calls League.loadWeeklyRosters when it calls Team.fetchWeeklyRoster
                                        # self.startingRosterSlots is constructed by League.buildTeams
        
    
    def __repr__(self):
        """ This is what is displayed when print(team) is entered"""
        return 'Team(%s)' % (self.teamName)     
        
    def nameOwner(self, owner):
        """owner = teams['members'][teamIndex]['firstName']"""
        self.owner = owner
        return
    
    def addMatchup(self, teamData, week):
        ''' Currently only adds a team's score for a given week to its scores{} attribute '''
        self.scores[week] = round(teamData['totalPoints'],1)    
        return

    def fetchWeeklyRoster(self, rosterData, week):
        '''Fetch the roster of a team for a specific week'''
        roster = rosterData['entries']                      # Get the players in roster{}
        self.rosters[week] = []                             # Create an empty list for the team roster for the given week
        for player in roster:
            self.rosters[week].append(Player(player))       # Add each player on the roster to team's roster for the given week
        
    ''' **************************************************
        *      Begin advanced stats team methods         *
        ************************************************** '''
    
    def topPlayers(self, week, slotCategoryId, n):
        ''' Takes a list of players and returns a list of the top n players based on points scored. '''
        # Gather players of the desired position
        unsortedList = []
        for player in self.rosters[week]:
            if slotCategoryId in player.eligibleSlots:
                unsortedList += [player]
                
        # Sort players by points scored
        sortedList = [unsortedList[0]]
        for player in unsortedList[1:]:
            for i in range(len(sortedList)):
                if (player.score >= sortedList[i].score):
                    sortedList = sortedList[:i] + [player] + sortedList[i:]
                    break
            if player not in sortedList:
                sortedList += [player]
        return sortedList[:n]       
    
    def bestLineup(self, week):
        ''' Returns the best possible lineup for team during a given week. '''
        savedRoster = self.rosters[week][:]
        
        # Find Best Lineup
        bestLineup = []
        for slotId in self.startingRosterSlots.keys():
            numPlayers = self.startingRosterSlots[slotId][0]
            bestPlayers = self.topPlayers(week, int(slotId), numPlayers)
            bestLineup += bestPlayers
            for player in bestPlayers:
                self.rosters[week].remove(player)
        self.rosters[week] = savedRoster 
        
        # Sum Scores
        maxScore = 0
        for player in bestLineup:
            maxScore += player.score          
        return round(maxScore, 2)   

    def bestTrio(self, week):
        ''' Returns the the sum of the top QB/RB/Reciever tri0 for a team during a given week. '''
        qb = self.topPlayers(week, 0, 1)[0].score
        rb = self.topPlayers(week, 2, 1)[0].score
        wr = self.topPlayers(week, 4, 1)[0].score
        te = self.topPlayers(week, 6, 1)[0].score
        bestTrio = round(qb + rb + max(wr, te), 2)
        return bestTrio 

    def getTeams(self):
        ''' Takes a team and returns all other teams in the league (in order of schedule, not team ID). ''' 
        opponents = self.schedule
        otherTeams = []
        for opp in opponents.values():
            if opp not in otherTeams:
                otherTeams += [opp]
        return otherTeams

    def weeklyFinish(self, week):
        ''' Returns the rank of a team based on the weekly score of a team for a given week. '''
        otherTeams = self.getTeams()
        weeklyFinish = 1
        for teamId in range(len(otherTeams)):
            if (self.scores[week] != otherTeams[teamId].scores[week]) and (self.scores[week] <= otherTeams[teamId].scores[week]):
                weeklyFinish += 1;
        return weeklyFinish  

    def numOut(self, week):
        ''' Returns the (esimated) number of players who did not play for a team during a given week (excluding IR slot players). '''
        numOut = 0
        # TODO: write new code based on if player was injured
        return numOut

    def avgStartingScore(self, week, slotId):
        count = 0
        sum = 0
        for p in self.rosters[week]:
            if (p.positionId == slotId) and (p.isStarting):
                count += 1
                sum += p.score
        avgScore = round(sum/count,2)
        return avgScore
    
    def totalBenchPoints(self, week):
        sum = 0
        for p in self.rosters[week]:
            if not p.isStarting:
                sum += p.score
        return sum
    
    def printWeeklyStats(self, week):
        ''' Print the weekly stats for the team during a given week. '''
        print( '----------------------------' + '\n' + \
            self.owner[0] + ' Week ' + str(week) + '\n' + \
            '----------------------------' + '\n' + \
            'Week Score: ' + str(self.scores[week]) + '\n' + \
            'Best Possible Lineup: ' + str(self.bestLineup(week)) + '\n' + \
            'Opponent Score: ' + str(self.schedule[week].scores[week]) + '\n' + \
            'Weekly Finish: ' + str(self.weeklyFinish(week)) + '\n' + \
            'Best Trio: ' + str(self.bestTrio(week)) + '\n' + \
            'Number of Injuries: ' + str(self.numOut(week)) + '\n' + \
            'Starting QB pts: ' + str(self.avgStartingScore(week, 0)) + '\n' + \
            'Avg. Starting RB pts: ' + str(self.avgStartingScore(week, 2)) + '\n' + \
            'Avg. Starting WR pts: ' + str(self.avgStartingScore(week, 4)) + '\n' + \
            'Starting TE pts: ' + str(self.avgStartingScore(week, 6)) + '\n' + \
            'Starting Flex pts: ' + str(self.avgStartingScore(week, 23)) + '\n' + \
            'Starting DST pts: ' + str(self.avgStartingScore(week, 16)) + '\n' + \
            'Starting K pts: ' + str(self.avgStartingScore(week, 17)) + '\n' + \
            'Total Bench pts: ' + str(self.totalBenchPoints(week)) + '\n' + \
            '----------------------------')    

class Player():
    """
    rosterData['teams'][team.teamId - 1]['roster']
    """
    def __init__(self, playerData):
        self.id = playerData['playerId']
        self.positionId = playerData['lineupSlotId']
        self.acquisitionType = playerData['acquisitionType']
        
        playerData = playerData['playerPoolEntry']
        self.score = playerData['appliedStatTotal']             # Points scored for the given week
        
        playerData = playerData['player']
        
        self.name = playerData['fullName']
        self.eligibleSlots = playerData['eligibleSlots']
        self.isStarting = self.positionId not in [20, 21, 24]
        self.injured = playerData['injured']
        self.nflTeamId = playerData['proTeamId']
        #self.rankings = playerData['rankings']                 # Don't need this... yet?
        #self.outlook = playerData['outlooks']                  # Words describing the outlook for this week
        #self.seasonOutlook = playerData['seasonOutlook']        # Words describing the outlook for the rest of the season
            
    def __repr__(self):
        """ This is what is displayed when print(player) is entered"""
        return 'Player(%s)' % (self.name)
        
''' ******************************************************************
    *                                                                *
    ****************************************************************** '''
        

username = 'desidezdez@gmail.com'
password = None;        
league_id = 1086064
espnAuth = '55B70875-0A4B-428F-B708-750A4BB28FA1'
espn_s2 = 'AEA2XITlUD5oV4FaNBbJ6vSaLZUJirSQoy7n9no%2BYrf0pEVcWac3tRNuqm2%2FoAH%2FuHCdPU1iiz%2Ba4ja%2Brv544LEZ859FGbTRnonPa8zbSDV6gCBaUahVbtfQCVoeL14qyK%2BNhb%2FqtRqVaL2r6jpKTUXEjzGBOHcBeo2s5a3PL7YmPM88ro73Usq4IGM%2BZf%2Fszl%2Fh%2FJatefzg4YJLzhG5dWT1HT23SRuMcTMT18so7WlqP%2F6oz%2FGCcz4tTzb1Xa02TvTeRF%2FcKUGbq%2FfY0JTSClDc'      

def getUrl(year, league_id):
    url = ''
    if (year >= 2019):         # ESPN API v3
        url = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/" + \
            str(year) + "/segments/0/leagues/" + str(league_id)
    else:                      # ESPN API v2
        url = "https://fantasy.espn.com/apis/v3/games/ffl/leagueHistory/" + \
            str(league_id) + "?seasonId=" + str(year)
    return url
        
matt_league_id_1 = 640928
matt_league_id_2 = 293050
matt_client = Authorize('mattricupero@gmail.com', 'mar627')

year = 2019
matt_cookies = {'swid' : matt_client.swid, 'espn_s2' : matt_client.espn_s2};
url = getUrl(year, matt_league_id_1)



if False:
    #matchups = requests.get(url, cookies = matt_cookies, params = {'view' : 'mMatchup'}).json()
    teams = requests.get(url, cookies = matt_cookies, params = {'view' : 'mTeam'}).json()
    #rosters = requests.get(url, cookies = matt_cookies, params = {'view' : 'mRoster'}).json()
    #settings = requests.get(url, cookies = matt_cookies, params = {'view' : 'mSettings'}).json()
    # kona = requests.get(url, cookies = auth, params = {'view' : 'kona_player_info'}).json()
    player_wl = requests.get(url, cookies = matt_cookies, params = {'view' : 'player_wl'}).json()
    # schedule = requests.get(url, cookies = auth, params = {'view' : 'mSchedule'}).json()
    # team = teams['teams'][0]


if True:
    leg = League(league_id, 2019, espnAuth, espn_s2)
    print(leg)

if False:
    leg = League(league_id, 2018)
    print(leg)

if False:
    leg = League(matt_league_id_1, 2019, matt_client.swid, matt_client.espn_s2)

if False:
    t = leg.teams[1]
    p =t.rosters[1][0]
    week = 1



'''    
matchups
    ['gameId']
    ['id']
    ['schedule'][0 - 47]
        ['away'] --or-- ['home']
           ['cumulativeScore']
           ['gamesPlayed']
           ['rosterForCurrentScoringPeriod']
               ['appliedStatTotal']            # Starting roster Score
               ['entries'][0 - 18]
                   ['acquisitionDate']
                   ['acquisitionType']
                   ['injuryStatus']
                   ['lineupSlotId']
                   ['pendingTransactionIds']
                   ['playerId']
                   ['playerPoolEntry']
                       ['appliedStatTotal']
                       ['id']
                       ['keeperValue']
                       ['keeperValueFuture']
                       ['lineupLocked']
                       ['onTeamId']
                       ['player']
                       ['rosterLocked']
                       ['status']
                       ['tradeLocked']
                   ['status']
           ['rosterForMatchupPeriod']
               ['appliedStatTotal']
               ['entries'][0 - 18]
                   ['acquisitionDate']
                   ['acquisitionType']
                   ['injuryStatus']
                   ['lineupSlotId']
                   ['pendingTransactionIds']
                   ['playerId']
                   ['playerPoolEntry']
                       ['appliedStatTotal']
                       ['id']
                       ['keeperValue']
                       ['keeperValueFuture']
                       ['lineupLocked']
                       ['onTeamId']
                       ['player']
                       ['rosterLocked']
                       ['status']
                       ['tradeLocked']
                   ['status']
           ['rosterForMatchupPeriodDelayed']
           ['teamId']                           # UKNOWN ORDER
           ['totalPoints'] 
        ['id']
        ['matchupPeriodId']
        ['winner']
    ['scoringPeriodId']
    ['seasonId']
    ['segmentId']
    ['status']
    ['teams'][0 - 7]
        ['id']                           # Team ID
        ['roster']
            ['appliedStatTotal']         # Starting Lineup Score  
            ['entries'][0 - 17]          # Full Roster
                ['acquisitionDate']
                ['acquisitionType']
                ['injuryStatus']
                ['lineupSlotId']
                ['pendingTransactionIds']
                ['playerId']
                ['playerPoolEntry']      # Player stats 
                    ['appliedStatTotal'] # Points scored
                    ['id']
                    ['keeperValue']
                    ['keeperValueFuture']
                    ['lineupLocked']
                    ['onTeamId']
                    ['player']
                        ['active']
                        ['defaultPositionId']
                        ['droppable']
                        ['eligibleSlots']
                        ['firstName']
                        ['fullName']
                        ['id']
                        ['injured']
                        ['injuryStatus']
                        ['lastName']
                        ['lastNewsDate']
                        ['lastVideoDate']
                        ['proTeamId']
                        ['rankings']
                        ['universeId']
                    ['rosterLocked']
                    ['status']
                    ['tradeLocked']
                ['status']
    
teams
    ['draftDetail']
    ['gameId']  
    ['id']                      # League ID
    ['members'][0 - 7]          # UNKOWN ORDER (Julia first)
        ['displayName']         # Owner user name
        ['firstName']           # Owner first name
        ['id']                  # SWID
        ['lastName']            # Owner last name
        ['notificationSettings']
    ['scoringPeriodId']
    ['seasonId']
    ['segmentId']  
    ['status'] 
    ['teams'][0 - 7]            # Desi first
        ['abbrev']
        ['currentProjectedRank']
        ['divisionId']
        ['draftDayProjectedRank']
        ['draftStrategy']
        ['id']                  # Team id = teamIndex + 1
        ['isActive']
        ['location']
        ['logo']
        ['logoType']
        ['nickname']
        ['owners']              # Owner SWID
        ['playoffSeed']
        ['points']
        ['pointsAdjusted']
        ['pointsDelta']
        ['primaryOwner']
        ['rankCalculatedFinal']
        ['rankFinal']
        ['record']
            ['away']
            ['division']
            ['home']
            ['overall']
                ['gamesBack']
                ['losses']
                ['percentage']
                ['pointsAgainst']
                ['pointsFor']
                ['streakLength']
                ['streakType']
                ['ties']
                ['wins']
        ['tradeBlock']
        ['transactionCounter']
        ['valuesByStat']
        ['waiverRank']
        
rosters:                                # Desi is teamId 1
    ['gameId']
    ['id']
    ['scoringPeriodId']
    ['seasonId']
    ['segmentId']
    ['status']
    ['teams'][0 - 7]
        ['id']                           # Team ID
        ['roster']                       
            ['appliedStatTotal']         # Starting Lineup Score  
            ['entries'][0 - 18]          # Full Roster
                ['acquisitionDate']
                ['acquisitionType']
                ['injuryStatus']
                ['lineupSlotId']
                ['pendingTransactionIds']
                ['playerId']
                ['playerPoolEntry']
                    ['appliedStatTotal']
                    ['id']
                    ['keeperValue']
                    ['keeperValueFuture']
                    ['lineupLocked']
                    ['onTeamId']
                    ['player']
                        ['active']
                        ['defaultPositionId']
                        ['draftRanksByRankType']
                        ['droppable']
                        ['eligibleSlots']
                        ['firstName']
                        ['fullName']
                        ['id']
                        ['injured']
                        ['injuryStatus']
                        ['lastName']
                        ['lastNewsDate']
                        ['lastVideoDate']
                        ['outlooks']
                        ['ownership']
                        ['proTeamId']
                        ['rankings']
                        ['seasonOutlook']
                        ['stats']
                        ['universeId']
                    ['ratings']
                    ['rosterLocked']
                    ['status']
                    ['tradeLocked']
                ['status']
            
settings
    ['draftDetail']
    ['gameId']
    ['id']                         # League ID
    ['scoringPeriodId']
    ['seasonId']
    ['segmentId']
    ['settings'] 
        ['acquisitionSettings']
        ['draftSettings']
        ['financeSettings']
        ['isCustomizable']
        ['isPublic']
        ['name']
        ['restrictionType']
        ['rosterSettings']
            ['isBenchUnlimited']
            ['isUsingUndroppableList']
            ['lineupLocktimeType']
            ['lineupSlotCounts']                   # STARTING ROSTER
            ['lineupSlotStatLimits']
            ['moveLimit']
            ['positionLimits']
            ['rosterLocktimeType']
            ['universeIds']
        ['status']
        ['scheduleSettings']
        ['scoringSettings']
        ['size']
        ['tradeSettings']
        
kona
# Gets list of every player, no good way to search it though
# Better for machine learning data than team info
    ['players'][0 - 1059]
        ['draftAuctionValue']
        ['id']
        ['keeperValue']
        ['keeperValueFuture']
        ['lineupLocked']
        ['onTeamId']
        ['player']
            ['active']
            ['defaultPositionId']
            ['draftRanksByRankType']
            ['droppable']
            ['eligibleSlots']
            ['firstName']
            ['fullName']
            ['id']
            ['injured']
            ['lastName']
            ['outlooks']
            ['ownership']
            ['proTeamId']
            ['rankings']
            ['seasonOutlook']
            ['stats'] 
        ['ratings']
        ['rosterLocked']
        ['status']
        ['tradeLocked']
    ['positionAgainstOpponent']
    
    
player_wl                      # Not really helpful)
    ['gameId']
    ['id']                     # League ID
    ['members']                # League members
    ['scoringPeriodId']        # Current week?
    ['seasonId']
    ['segmentId']
    ['settings']               # League name
    ['status']
    ['teams'][0 - 7]
        ['abbrev']
        ['id']
        ['location']
        ['nickname']
        ['owners']             # SWID
        
        
schedule
    ['activatedDate']
    ['createdAsLeagueType']
    ['currentLeagueType']
    ['currentMatchupPeriod']
    ['finalScoringPeriod']
    ['firstScoringPeriod']
    ['isActive']
    ['isExpired']
    ['isFull']
    ['isPlayoffMatchupEdited']
    ['isToBeDeleted']
    ['isViewable']
    ['isWaiverOrderEdited']
    ['latestScoringPeriod']
    ['previousSeasons']
    ['standingsUpdateDate']
    ['teamsJoined']
    ['transactionScoringPeriod']
    ['waiverLastExecutionDate']
    ['waiverProcessStatus']

        
'''