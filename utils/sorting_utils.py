''' 
**************************************************
*    Stat sortitng methods for League class      *
************************************************** 
'''  

def sortWeeklyScore(league, week):
    ''' Sorts league teams for a given week based on weekly score (highest score is first). '''
    teams = league.dictValuesToList(league.teams)      
    sortedTeams = sorted(teams, key=lambda x: x.scores[week],
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict


def sortBestLineup(league, week):
    ''' Sorts league teams for a given week based on best possible lineup (highest score is first). '''
    teams = league.dictValuesToList(league.teams)      
    sortedTeams = sorted(teams, key=lambda x: x.bestLineup(week),
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict   

def sortOpponentScore(league, week):
    ''' Sorts league teams for a given week based on their opponent's score (highest opponent score is first). '''
    teams = league.dictValuesToList(league.teams)      
    sortedTeams = sorted(teams, key=lambda x: x.schedule[week].scores[week],
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict

def sortBestTrio(league, week):
    ''' Sorts league teams for a given week based on their best QB/RB/Receiver trio (highest score is first). '''
    teams = league.dictValuesToList(league.teams)      
    sortedTeams = sorted(teams, key=lambda x: x.bestTrio(week),
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict

def sortNumOut(week):
    ''' Sorts league teams for a given week based on the number of players who did not play (least injuries is first). '''
    teams = league.dictValuesToList(league.teams)      
    sortedTeams = sorted(teams, key=lambda x: x.numOut(week),
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict

def sortPositionScore(league, week, slotId):
    ''' Sorts league teams for a given week based on the average starting slotId points (highest score is first) '''  
    teams = league.dictValuesToList(league.teams)
    sortedTeams = sorted(teams, key=lambda x: x.avgStartingScore(week, slotId),
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict    

def sortBenchPoints(league, week):
    ''' Sorts league teams for a given week based on the total bench points (highest score is first). '''
    teams = league.dictValuesToList(league.teams)
    sortedTeams = sorted(teams, key=lambda x: x.totalBenchPoints(week),
                          reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict       

def sortDifference(league, week):
    ''' Sorts league teams for a given week based on the the difference between their 
    best possible score and their actual score (lowest difference is first). '''
    teams = league.dictValuesToList(league.teams)
    sortedTeams = sorted(teams, key=lambda x: x.scores[week] - x.schedule[week].scores[week], reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict      

def sortOverallRoster(league, week):
    ''' Sorts league teams for a given week based on total roster points (highest score is first). '''
    teams = league.dictValuesToList(league.teams)
    sortedTeams = sorted(teams, key=lambda x: (x.totalBenchPoints(week) + x.scores[week]), reverse=True)
    ranks = list(range(1, league.numTeams + 1))
    sortedTeamDict = league.listsToDict(ranks, sortedTeams)
    return sortedTeamDict        