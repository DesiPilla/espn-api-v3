# Packages for fetching ESPN credentials
from authorize import get_credentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidArgumentException

# Packages for building League
from team import Team
from utils.building_utils import *
from utils.sorting_utils import *
from utils.printing_utils import *

import requests
import numpy as np
import pandas as pd
import scipy as sp
from scipy import stats
from tabulate import tabulate as table
import matplotlib.pyplot as plt

class League():
    
    def __init__(self, league_id, year, username=None, password=None, swid=None, espn_s2=None):
        self.league_id = league_id
        self.year = year
        
        self.username = username
        self.password = password
        
        new_league = False
        if (swid is not None) and (espn_s2 is not None):
            self.swid = swid
            self.espn_s2 = espn_s2
        else:
            # Get ESPN credentials
            self.swid, self.espn_s2 = get_credentials()
            new_league = True

        # Build league week-by-week
        buildLeague(self)
        
        # Save ESPN credentials
        if new_league:
            try:
                login = pd.read_csv('login.csv').iloc[:, 1:]
            except:
                login = pd.DataFrame(columns=['manager', 'league_name', 'league_id', 'swid', 'espn_s2'])
            creds = {'manager':self.teams[1].owner, 'league_name':self.settings['name'], 'league_id':self.league_id, 'swid':self.swid, 'espn_s2':self.espn_s2}
            login = login.append(creds, ignore_index=True)
            login.to_csv('login.csv', index=False) 
            print("[BUILDING LEAGUE] League credentials saved.")
            
        return
        
        
    def __repr__(self):
        """This is what is displayed when print(league) is entered """
        return 'League(%s, %s)' % (self.settings['name'], self.year, ) 
 
    
    ''' **************************************************
        *             Begin printing methods             *
        ************************************************** '''
    
    def printWeeklyScores(self, teamId):
        printWeeklyScores(self, teamId)
        return
    
    def printWeeklyMatchResults(self, teamId):
        printWeeklyMatchResults(self, teamId)
        return
    
    def printPowerRankings(self, week):
        return printPowerRankings(self, week)
        
    def printLuckIndex(self, week):
        return printLuckIndex(self, week)
    
    def printCurrentStandings(self):
        return printCurrentStandings(self)
    
    def printExpectedStandings(self, week):
        return printExpectedStandings(self, week)
    
    def printWeeklyStats(self, week):
        return printWeeklyStats(self, week)

    
    ''' **************************************************
        *         Begin advanced stats methods           *
        ************************************************** '''
    
    def weeklyScore(self, teamId, week):
        ''' Returns the number of points scored by a team's starting roster for a given week. '''
        if week <= self.currentWeek:
            return self.teams[teamId].scores[week]
        else:
            return None
        
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
           
    def bestTrio(self, teamId, week):
        ''' Returns the the sum of the top QB/RB/Reciever trio for a team during a given week. '''
        qb = self.topPlayers(teamId, week, 0, 1)[0].score
        rb = self.topPlayers(teamId, week, 2, 1)[0].score
        wr = self.topPlayers(teamId, week, 4, 1)[0].score
        te = self.topPlayers(teamId, week, 6, 1)[0].score
        bestTrio = round(qb + rb + max(wr, te), 2)
        return bestTrio  
    
    def weeklyFinish(self, teamId, week):
        ''' Returns the rank of a team based on the weekly score of a team for a given week. '''
        team = self.teams[teamId]                           # Get the Team object associated with the input teamId
        teamIds = list(range(1, self.numTeams + 1))         # Get a list of teamIds 
        teamIds.remove(team.teamId)                         # Remove the teamId of the working team from the list of teamIds
        weeklyFinish = 1                                    # Initialize the weeklyFinish to 1
        for teamId in teamIds:
            if (team.scores[week] != self.teams[teamId].scores[week]) and (team.scores[week] <= self.teams[teamId].scores[week]):
                weeklyFinish += 1;                          # Increment the weeklyFinish for every team with a higher weekly score
        return weeklyFinish
    
    def averageWeeklyFinish(self, teamId, week):
        ''' This function returns the average weekly finish of a team through a certain week '''
        finish = 0
        for wk in range(1, week + 1):
            finish += self.weeklyFinish(teamId, wk)
        return finish / week    
    
    def averageOpponentFinish(self,  teamId, week):
        ''' This function returns the average weekly finish of a team's weekly opponent through a certain week '''
        finish = 0
        for wk in range(1, week + 1):
            finish += self.weeklyFinish(self.teams[teamId].schedule[wk].teamId, wk)
        return finish / week     
    
    def teamWeeklyPRank(self, teamId, week):
        ''' Returns the power rank score of a team for a certain week. '''
        team = self.teams[teamId]
        
        # Points for score
        bestWeeklyScore = sortWeeklyScore(self, week)[1].scores[week]
        score = self.weeklyScore(teamId, week)
        pfScore = score / bestWeeklyScore * 70
        
        '''
        # Team Record score (REDACTED - replaced with 'Team Weekly Finish Score')
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
        multiplier = 1 + (win + luck) / 200
        '''
        
        # Team Weekly Finish Score
        place = self.weeklyFinish(teamId, week)
        if place <= self.numTeams / 2:
            win = 5            # Team deserved to be one of the winning teams
        else:
            win = 0             # Team didn't deserve to be one of the winning teams
        multiplier = 1 + (win) / 100        
        
        # Best lineup score
        bestScore = team.bestLineup(week)    # Best possible lineup for team
        bestBestWeeklyScore = sortBestLineup(self, week)[1].scores[week]
        bestLineupScore = bestScore / bestBestWeeklyScore * 20
        
        '''(REDACTED)
        # Dominance score
        if score > oppScore:
            dominance = (score - oppScore) / score * 10
        else:
            dominance = 0
        '''    
        
        return pfScore*multiplier + bestLineupScore
    
    def teamTotalPRank(self, teamId, week):
        ''' Gets overall power ranking for a team. ''' 
        if week >= self.currentWeek:
            week = self.currentWeek - 1        
        
        pRank = 0
        for wk in range(1, week+1):
            pRank += self.teamWeeklyPRank(teamId, wk)
        pRank += self.teamWeeklyPRank(teamId, week)*2
        if week > 1:
            pRank += self.teamWeeklyPRank(teamId, week-1)
            week += 1
        return pRank / (week + 2)
    
    def weeklyLuckIndex(self, teamId, week):
        ''' This function returns an index quantifying how 'lucky' a team was in a given week '''
        team = self.teams[teamId]
        opp = team.schedule[week]
    
        # Luck Index based on where the team and its opponent finished compared to the rest of the league  
        result = team.weeklyResult(week)
        place = self.weeklyFinish(teamId, week)
        if result == 1:                                 # If the team won...
            odds = (place - 1) / (self.numTeams - 2)    # Odds of this team playing a team with a higher score than it
            luckIndex = 5*odds                          # The worse the team ranked, the luckier they were to have won
        else:                                                           # if the team lost or tied...
            odds = (self.numTeams - place) / (self.numTeams - 2)    # Odds of this team playing a team with a lower score than it
            luckIndex = -5*odds                                          # The better the team ranked, the unluckier they were to have lost or tied
        if result == 0.5:                               # If the team tied...
            luckIndex /= 2                              # They are only half as unlucky, because tying is not as bad as losing
            
        # Luck Index based on how the team scored compared to its opponent
        teamScore = team.scores[week]
        avgScore = team.avgPointsFor(week)
        stdevScore = team.stdevPointsFor(week)
        if stdevScore != 0:
            zTeam = (teamScore - avgScore) / stdevScore     # Get z-score of the team's performance
            effect = zTeam/(3*stdevScore)*2                 # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
            luckIndex += (effect / abs(effect)) * min(abs(effect), 2)   # The maximum effect is +/- 2
        
        oppScore = opp.scores[week]
        avgOpp = opp.avgPointsAllowed(week)
        stdevOpp = opp.stdevPointsAllowed(week)
        if stdevOpp != 0:
            zOpp = (oppScore - avgOpp) / stdevOpp                       # Get z-score of the opponent's performance
            effect = zOpp/(3*stdevOpp)*2                        # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index     
            luckIndex -= (effect / abs(effect)) * min(abs(effect), 2)   # The maximum effect is +/- 2
      
        return luckIndex
                         
    def seasonLuckIndex(self, teamId, week):
        ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
        luckIndex = 0
        for week in range(1, week + 1):
            luckIndex += self.weeklyLuckIndex(teamId, week)
        return luckIndex    
    
    def resultsTopHalf(self, teamId, week):
        ''' This function returns the number of wins and losses a team would have through a certain week
        if a win was defined as scoring in the top half of teams for that week. I.e., in an 8 person league, the
        4 teams that scored the most points would be granted a win, and the other 4 teams would be granted a loss.'''
        wins, losses = 0, 0
        for wk in range(1, week + 1):
            place = self.weeklyFinish(teamId, wk)
            if place <= self.numTeams // 2:
                wins += 1
            else:
                losses += 1
        return wins, losses        
    
    def expectedFinish(self, teamId, week):
        ''' Inputs: teamId, week (that just passed)
            Returns: numWins, numLosses, numTies
            This function estimates the results of every remaining matchup for a team
            based on the team's and its opponent's power ranking. These results are 
            added to the team's current matchup results.
        '''
        team = self.teams[teamId]
        wins = team.wins
        losses = team.losses
        ties = team.ties
        pRank = self.teamTotalPRank(teamId, week)
        for wk in range(week + 1, self.regSeasonWeeks + 1):
            oppId = self.getTeamId(team.schedule[wk])
            oppPRank = self.teamTotalPRank(oppId, week)
            if pRank > oppPRank:
                wins += 1
            elif pRank < oppPRank:
                losses += 1
            else:
                ties += 1
        return wins, losses, ties  
        
    def getTeamId(self, team):
        ''' Inputs: Team object
            Outputs: teamId
            This function finds and returns the teamId of a Team object
        '''
        for i in range(1, self.numTeams + 1):
            if self.teams[i] == team:
                return self.teams[i].teamId

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
    
    def getPRanksList(self, teamId, week):
        '''
        Inputs: int (teamId), int (week)
        Outputs: list of floats (power rank of the team for each week through week (inclusive))
        
        This function takes a teamId and week as inputs and returns a list containing
        the team's power rank for each week up to and including the input week.
        '''
        pRanks = []
        for wk in range(1, week + 1):
            pRanks.append(self.teamTotalPRank(teamId, wk))
        return pRanks     
    
    
    def pWin_score(self, teamId, week):
        '''
        Inputs: int (teamId), int (week of matchup)
        Output: float (probability that team will win)
        
        This function takes in a team id and the week of the matchup and returns
        the probability that the team will win the matchup. This probability is
        caluclated by subtracting the probability distribution functions of the
        team's score and its opponent's score. The pdf's are assumed to follow a
        normal distribution for both teams.
        '''
        team = self.teams[teamId]
        avgScore = team.avgPointsFor(week - 1);
        stdScore = team.stdevPointsFor(week - 1)
        
        avgOpp = team.schedule[week].avgPointsFor(week - 1)
        stdOpp = team.schedule[week].stdevPointsFor(week - 1)
        
        return sp.stats.norm(avgScore - avgOpp, np.sqrt(stdScore**2 + stdOpp**2)).sf(0)
    
    def pWin_pRank(self, teamId, week):
        '''
        Inputs: int (teamId), int (week of matchup)
        Output: float (probability that team will win)
        
        This function takes in a team id and the week of the matchup and returns
        the probability that the team will win the matchup. This probability is
        caluclated by subtracting the probability distribution functions of the
        team's power rank and its opponent's power rank. The pdf's are assumed 
        to follow a normal distribution for both teams.
        '''
        team = self.teams[teamId]
        pRanks = self.getPRanksList(teamId, week)
        
        oppPranks = []
        for wk in range(1, week):
            oppPranks.append(self.teamTotalPRank(team.schedule[wk].teamId, wk))
        
        avgScore = np.mean(pRanks)
        stdScore = np.std(pRanks)
        avgOpp = np.mean(oppPranks)
        stdOpp = np.std(oppPranks)
        
        return sp.stats.norm(avgScore - avgOpp, np.sqrt(stdScore**2 + stdOpp**2)).sf(0)    
    
    def checkAccuracy(self, week, function):
        '''
        Inputs: int (week), function (to predict matchup result)
        Outputs: float (accuracy of model)
        
        This function checks the accuracy of the input pWin function.
        It calls the function for every matchup that through (inclusive) the
        input week and compares the expected result with the actual result.
        The final accuracy is determined by taking the percentage of correctly
        prediced results.
        '''
        if week >= self.currentWeek:
            week = self.currentWeek - 1
            
        numMatchups = 0
        numCorrect = 0
        for team in self.teams.values():
            for wk in range(2, week + 1):
                actualResult = team.weeklyResult(wk)
                predictedResult = round(function(team.teamId, wk), 0)
                if actualResult == predictedResult:
                    numCorrect += 1
                numMatchups += 1
        return numCorrect/2, numMatchups/2, numCorrect / numMatchups
    
    def plotPRanks(self, week):
        if week >= self.currentWeek:
            week = self.currentWeek - 1
        
        fig = plt.figure()
        graph = fig.add_subplot(1, 2, 1)
        wks = list(range(1, week + 1))
        for teamId in self.teams:
            pRanks = self.getPRanksList(teamId, week)
            plt.plot(wks, pRanks, '-', label=self.teams[teamId].teamName)
        plt.title("Power Rankings vs Week")
        plt.xlabel("Week")
        plt.ylabel("Power Rank")
        plt.legend(loc=9, bbox_to_anchor = (1.4, 1))         
        fig.set_size_inches(10, 4)
        plt.hold = False 
        return
        
        