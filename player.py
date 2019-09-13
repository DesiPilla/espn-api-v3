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