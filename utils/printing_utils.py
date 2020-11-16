from .sorting_utils import *
from tabulate import tabulate as table

'''
**************************************************
*       Printing methods for League class        *
**************************************************
'''

def printWeeklyScores(league, teamId):
    ''' Prints all weekly scores for a given team. '''
    print('  ---',league.teams[teamId].teamName,'---')
    for week in range(1, league.currentWeek):
        score = league.weeklyScore(teamId, week)
        print('Week ', week, ': ', round(score, 1))
    sum = 0
    for i in range(1, league.currentWeek):
        sum += league.teams[teamId].scores[i]
    avg = sum/ (league.currentWeek - 1)
    print('-------------------------------','\nAvg. Score:', '%.2f' % avg)
    return

def printWeeklyMatchResults(league, teamId):
    ''' Prints all weekly match results for a given team. '''
    team = league.teams[teamId]
    print('  ---',team.teamName,'---')
    for week in range(1, league.currentWeek):
        print('Week',str(week+1),': ', end ="")
        print('%.2f' % team.scores[week], '-', '%.2f' % team.schedule[week].scores[week], end='')
        print('   vs.', team.schedule[week].owner)
    print('------------------------------------------------------------')
    print('Season Record:',str(team.wins),'-',str(team.losses),'-',str(team.ties))

def printPowerRankings(league, week):
    ''' Print my power rankings in a nice table. '''
    powerRankings = []
    for teamId in range(1, league.numTeams + 1):
        powerRankings += [[league.teamTotalPRank(teamId, week), league.teams[teamId]]]
    sortedRankings = sorted(powerRankings, key=lambda x: x[0], reverse=True)
    powerRankingsTable = []
    for team in sortedRankings:
        powerRankingsTable += [[ team[1].teamName, team[0], team[1].owner ]]
    print('\n','Week ',week)
    print(table( powerRankingsTable, headers = ['Team', 'Power Index', 'Owner'], floatfmt = '.2f', tablefmt='github'))
    return powerRankingsTable

def printLuckIndex(league, week):
    ''' This function prints the index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    lucks = []
    for teamId in range(1, league.numTeams + 1):
        luck = league.seasonLuckIndex(teamId, week)
        lucks.append([league.teams[teamId].teamName, round(luck, 2), league.teams[teamId].owner])
    lucks.sort(key = lambda x: x[1], reverse = True)
    print('\nThrough Week %d'% (week))
    print(table(lucks, headers = ["Team", "Luck Index", "Owner"], tablefmt='github'))
    return lucks

def printCurrentStandings(league):
    ''' Inputs: None
        Outputs: table (prints current standings)
        This function prints the current standings for a league.
        This function does NOT account for tiebreakers.
    '''
    results = []
    for teamId in range(1, league.numTeams + 1):
        wins = league.teams[teamId].wins
        losses = league.teams[teamId].losses
        ties = league.teams[teamId].ties
        pf = league.teams[teamId].pointsFor
        results += [[league.teams[teamId], wins, losses, ties, pf]]
    results.sort(key=lambda x: x[4], reverse=True)              # Sort first based on points for
    results.sort(key=lambda x: x[1], reverse=True)              # Sort second based on win total
    results.sort(key=lambda x: x[2], reverse=False)             # Sort third based on loss total
    resultsTable = []
    for team in results:
        resultsTable += [[ team[0].teamName, team[1], team[2], team[3], team[4], team[0].owner ]]
    print('\nWeek', league.currentWeek, '\n', table( resultsTable, headers = ['Team', 'Wins', 'Losses', 'Ties', 'Points Scored', 'Owner'], floatfmt = '.2f'), '\n\n*These standings do not account for tiesbreakers')
    return resultsTable

def printExpectedStandings(league, week):
    ''' Inputs: week that just passed
        Outputs: table (prints expected standings)
        This function predicts the expected final standings for a league based
        on the power rankings through a given week.
        This function does NOT account for tiebreakers.
    '''
    results = []
    for teamId in range(1, league.numTeams + 1):
        wins, losses = league.expectedFinish(teamId, week)
        results += [[league.teams[teamId], wins, losses]]
    results.sort(key=lambda x: x[1], reverse=True)              # Sort first based on win total
    results.sort(key=lambda x: x[2], reverse=False)             # Sort second based on loss total
    resultsTable = []
    for team in results:
        resultsTable += [[ team[0].teamName, team[1], team[2], team[0].owner ]]
    print('\nWeek', week)
    print(table( resultsTable, headers = ['Team', 'Wins', 'Losses', 'Owner'], floatfmt = '.2f', tablefmt='github'), '\n\n*These standings do not account for tiebreakers')
    return resultsTable

def printWeeklyStats(league, week):
    ''' Prints weekly stat report for a league during a given week. '''
    last = league.numTeams
    statsTable = [['Most Points Scored: ', sortWeeklyScore(league, week)[1].owner],
                   ['Least Points Scored: ', sortWeeklyScore(league, week)[last].owner],
                   ['Best Possible Lineup: ', sortBestLineup(league, week)[1].owner],
                   ['Best Trio: ', sortBestTrio(league, week)[1].owner],
                   ['Worst Trio: ', sortBestTrio(league, week)[last].owner],
                   ['Best Lineup Setter', sortDifference(league, week)[1].owner],
                   ['Worst Lineup Setter', sortDifference(league, week)[last].owner],
                   ['---------------------','----------------'],
                   ['Best QBs: ', sortPositionScore(league, week, 0)[1].owner],
                   ['Best RBs: ', sortPositionScore(league, week, 2)[1].owner],
                   ['Best WRs: ', sortPositionScore(league, week, 4)[1].owner],
                   ['Best TEs: ', sortPositionScore(league, week, 6)[1].owner],
                   ['Best Flex: ', sortPositionScore(league, week, 23)[1].owner],
                   ['Best DST: ', sortPositionScore(league, week, 16)[1].owner],
                   ['Best K: ', sortPositionScore(league, week, 17)[1].owner],
                   ['Best Bench: ', sortBenchPoints(league, week)[1].owner],
                   ['---------------------','----------------'],
                   ['Worst QBs: ', sortPositionScore(league, week, 0)[last].owner],
                   ['Worst RBs: ', sortPositionScore(league, week, 2)[last].owner],
                   ['Worst WRs: ', sortPositionScore(league, week, 4)[last].owner],
                   ['Worst TEs: ', sortPositionScore(league, week, 6)[last].owner],
                   ['Worst Flex: ', sortPositionScore(league, week, 23)[last].owner],
                   ['Worst DST: ', sortPositionScore(league, week, 16)[last].owner],
                   ['Worst K: ', sortPositionScore(league, week, 17)[last].owner],
                   ['Worst Bench: ', sortBenchPoints(league, week)[last].owner]]
    print('\n', table(statsTable, headers = ['Week ' + str(week), '']))

    # ['Most Injuries: ', league.sortNumOut(week)[last].owner.split(' ')[0]],
    # ['Least Injuries: ', league.sortNumOut(week)[0].owner.split(' ')[0]],
    return statsTable
