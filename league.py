from authorize import Authorize
from team import Team
import requests
from tabulate import tabulate as table

class League():
    
    def __init__(self, league_id, year, username = None, password = None):
        self.league_id = league_id
        self.year = year
        if username and password:
            client = Authorize(username, password)
            self.swid = client.swid
            self.espn_s2 = client.espn_s2
        else:
            self.swid = None
            self.espn_s2 = None            

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
            self.teamNames[teamId] = owner                          # Populate the teamNames dictionary
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
        stats_table = [['Most Points Scored: ', self.sortWeeklyScore(week)[1].owner.split(' ')[0]],
                       ['Least Points Scored: ', self.sortWeeklyScore(week)[last].owner.split(' ')[0]],
                       ['Best Possible Lineup: ', self.sortBestLineup(week)[1].owner.split(' ')[0]],
                       ['Best Trio: ', self.sortBestTrio(week)[1].owner.split(' ')[0]],
                       ['Worst Trio: ', self.sortBestTrio(week)[last].owner.split(' ')[0]],
                       
                       ['---------------------','----------------'],
                       ['Best QBs: ', self.sortPositionScore(week, 0)[1].owner.split(' ')[0]],
                       ['Best RBs: ', self.sortPositionScore(week, 2)[1].owner.split(' ')[0]],
                       ['Best WRs: ', self.sortPositionScore(week, 4)[1].owner.split(' ')[0]], 
                       ['Best TEs: ', self.sortPositionScore(week, 6)[1].owner.split(' ')[0]],
                       ['Best Flex: ', self.sortPositionScore(week, 23)[1].owner.split(' ')[0]],
                       ['Best DST: ', self.sortPositionScore(week, 16)[1].owner.split(' ')[0]],
                       ['Best K: ', self.sortPositionScore(week, 17)[1].owner.split(' ')[0]],
                       ['Best Bench: ', self.sortBenchPoints(week)[1].owner.split(' ')[0]],
                       ['---------------------','----------------'],
                       ['Worst QBs: ', self.sortPositionScore(week, 0)[last].owner.split(' ')[0]],
                       ['Worst RBs: ', self.sortPositionScore(week, 2)[last].owner.split(' ')[0]],
                       ['Worst WRs: ', self.sortPositionScore(week, 4)[last].owner.split(' ')[0]], 
                       ['Worst TEs: ', self.sortPositionScore(week, 6)[last].owner.split(' ')[0]],
                       ['Worst Flex: ', self.sortPositionScore(week, 23)[last].owner.split(' ')[0]],
                       ['Worst DST: ', self.sortPositionScore(week, 16)[last].owner.split(' ')[0]],
                       ['Worst K: ', self.sortPositionScore(week, 17)[last].owner.split(' ')[0]],
                       ['Worst Bench: ', self.sortBenchPoints(week)[last].owner.split(' ')[0]]]
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
    
    def printPowerRankings(self, week):
        ''' Print my power rankings in a nice table. '''
        powerRankings = []
        for teamId in range(1, self.numTeams + 1):
            powerRankings += [[self.teamTotalPRank(teamId, week), self.teams[teamId]]]
        sortedRankings = sorted(powerRankings, key=lambda x: x[0], reverse=True)        
        powerRankingsTable = []
        for team in sortedRankings:
            powerRankingsTable += [[ team[1].teamName,
                                       team[0],
                                       team[1].owner ]]
        print('\n','Week ',week, '\n', table( powerRankingsTable, headers = ['Power Index', 'Team', 'Owner'], floatfmt = '.2f')) 
