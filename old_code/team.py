import numpy as np
from player import Player
from tabulate import tabulate as table

class Team():
    """
    teamData['teams'][teamId]
    rosterData['schedule'][matchupNum]['home' or 'away']
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
    
    def addMatchup(self, teamData, week, year):
        ''' Currently only adds a team's score for a given week to its scores{} attribute 
        >= 2019: teamData = matchupData['schedule'][m]['away' or 'home']
        < 2019:  teamData = rosterData['teams'][teamId - 1]['roster']
        '''
        if year >= 2019:
            self.scores[week] = round(teamData['totalPoints'],1)   
            self.fetchWeeklyRoster(teamData['rosterForCurrentScoringPeriod']['entries'], week)
        else:
            self.fetchWeeklyRoster(teamData, week)
            self.scores[week] = 0
            for p in self.rosters[week]:
                if p.isStarting:
                    self.scores[week] += p.score
        
        return

    def fetchWeeklyRoster(self, rosterData, week):
        '''Fetch the roster of a team for a specific week
        rosterData = matchupData['schedule'][matchupNum]['home' or 'away']['rosterForCurrentScoringPeriod']['entries']
        '''
        self.rosters[week] = []                             # Create an empty list for the team roster for the given week
        for player in rosterData:
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
        count = max(count, 1)
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
        statsTable = [['Week Score: ', self.scores[week]],
                      ['Best Possible Lineup: ', self.bestLineup(week)],
                      ['Opponent Score: ', self.schedule[week].scores[week]],
                      ['Weekly Finish: ', self.weeklyFinish(week)],
                      ['Best Trio: ', self.bestTrio(week)],
                      ['Number of Injuries: ', self.numOut(week)],
                      ['Starting QB pts: ', self.avgStartingScore(week, 0)],
                      ['Avg. Starting RB pts: ', self.avgStartingScore(week, 2)],
                      ['Avg. Starting WR pts: ', self.avgStartingScore(week, 4)],
                      ['Starting TE pts: ', self.avgStartingScore(week, 6)],
                      ['Starting Flex pts: ', self.avgStartingScore(week, 23)],
                      ['Starting DST pts: ', self.avgStartingScore(week, 16)],
                      ['Starting K pts: ', self.avgStartingScore(week, 17)],
                      ['Total Bench pts: ', self.totalBenchPoints(week)]]
        print('\n', table(statsTable, headers = ['Week ' + str(week), ''], numalign = 'left'))   

    
    def weeklyResult(self, week):
        ''' For a given week:
                if the team lost, return 0
                if the team won, return 1
                if the team ties, return 0.5
        '''        
        oppScore = self.schedule[week].scores[week]
        if self.scores[week] < oppScore:
            return 0
        elif self.scores[week] > oppScore:
            return 1
        else:
            return 0.5
        
    def avgPointsFor(self, week):
        ''' This function returns the average points scored by the team through a certain week. '''
        return np.average(list(self.scores.values())[:week])
    
    def stdevPointsFor(self, week):
        ''' This function returns the standard deviation of the points scored by the team through a certain week. '''
        return np.std(list(self.scores.values())[:week])
    
    def avgPointsAllowed(self, week):
        ''' This function returns the average points scored by the team's opponents through a certain week. '''
        score = 0
        for wk in range(1, week + 1):
            score += self.schedule[wk].scores[wk]
        return score / week  
    
    def stdevPointsAllowed(self, week):
        ''' This function returns the standard deviation of the points scored by the team's opponents through a certain week. '''
        scores = []
        for wk in range(1, week + 1):
            scores += [self.schedule[wk].scores[wk]]
        return np.std(scores)
    
    def avgLineupSetting(self, week):
        ''' This function returns the average difference between the team's best possible score
        and their actual score. Higher values mean the team's lineup was less optimized. '''
        difference = 0
        for wk in range(1, week + 1):
            difference += self.bestLineup(wk) - self.scores[wk]
        return difference / week              
    
    def resultsBothTeamsBest(self, week):
        ''' This function returns the number of wins, losses, and ties the team should have,
        if both the team and its opponent played their best possible lineup each week. '''
        wins, losses, ties = 0, 0, 0
        for wk in range(1, week + 1):
            maxScore = self.bestLineup(wk)
            oppScore = self.schedule[wk].bestLineup(wk)
            if maxScore > oppScore:
                wins += 1
            elif maxScore < oppScore:
                losses += 1
            else:
                ties += 1
        return wins, losses, ties
    
    def resultsTeamBest(self, week):
        ''' This function returns the number of wins, losses, and ties the team should have
        if the team played their best possible lineup each week and their opponent's lineup was unchanged. '''
        wins, losses, ties = 0, 0, 0
        for wk in range(1, week + 1):
            maxScore = self.bestLineup(wk)
            oppScore = self.schedule[wk].scores[wk]
            if maxScore > oppScore:
                wins += 1
            elif maxScore < oppScore:
                losses += 1
            else:
                ties += 1
        return wins, losses, ties  
    
    