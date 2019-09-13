# espn-api-v3

This project aims to make ESPN Fantasy Football statistics easily available. 
With the introduction of version 3 of the ESPN's API, this structure creates leagues, teams, and player classes that allow for advanced data analytics and the potential for many new features to be added.

I am new to the Git interface, but any recommendations and pull requests are welcome.

This project was inspired and based off of [rbarton65/espnff](https://github.com/rbarton65/espnff)

Additional help/ideas were received from [cwendt94/ff-espn-api](https://github.com/cwendt94/ff-espn-api)


## Fetch public leagues
By typing your script into the main.py file:
```python
league_id = 1234
year = 2019
league = League(league_id, year)
```

## Fetch private leagues
By typing your script into the main.py file:
```python
league_id = 1234
year = 2019
user = yourusername@website.com
pass = yourPassword
league = League(league_id, year, user, pass)
```

## View league information
```python
>>> league.year
2019
>>> league.currentWeek
2
>>> league.regSeasonWeeks
12
>>> self.numTeams
8
>>> league.teamNames
{1: ['John Smith', 'T.Y. Very Much'], 2: ['Jane Doe', 'Home Sweet Mahomes'], ... teamId: [owner name, team name]}
>>> league.teams
{1: Team(T.Y. Very Much), 2: Team(Home Sweet Mahomes), ... teamId: Team(Team n Name)}
```

## View team information
```python
>>> team = league.teams[1]
Team(T.Y. Very Much')
>>> team.owner
'John Smith'
>>> team.teamName
'T.Y. Very Much'
>>> team.abbrev
'TYVM'
>>> team.wins
2
>>> team.losses
0
>>> team.schedule
{1: Team(Home Sweet Mahomes), 2: Team(Can you Diggs this?), .... weekNum: Team(opponentName) }
>>> team.scores
{1: 163.7, 2: 124.2, ... weekNum: score }
```
Under team.rosters, each value in the dictionary contains a list of player objects that relate to the team's roster for the given week.
```python
>>> team.rosters
{1: [Player(Ezekiel Elliot), Player(Kyler Murray), .....], 2: [Player(Todd Gurley), Player(Kyler Murray) .... ] 
```

## View player information
```python
>>> player = team.rosters[1][0]
>>> player.name
'Ezekiel Elliot'
>>> player.id
3051392
>>> player.eligibleSlots	# position slot ids that the player can be placed in
[2, 3, 23, 7, 20, 21]
>>> player.positionId		# position slot id that the user used him in
2
>>> player.isStarting
True
```

## View stats for a specific week
The two main purposes for this package is to be able to quickly and seamlessly view stats for a team or league that ESPN doesn't readily compute.
Using the 'printWeeklyStats' method, you can view a weekly report for a certain week.
```python
>>> team.printWeeklyStats(1)
----------------------------
John Smith Week 1
----------------------------
Week Score: 149.9
Best Possible Lineup: 156.42
Opponent Score: 116.5
Weekly Finish: 3
Best Trio: 74.32
Number of Injuries: 0
Starting QB pts: 30.72
Avg. Starting RB pts: 23.6
Avg. Starting WR pts: 9.85
Starting TE pts: 5.7
Starting Flex pts: 19.6
Starting DST pts: 10.0
Starting K pts: 17.0
Total Bench pts: 71.12
----------------------------
>>> league.printWeeklyStats(1)
 Week 1
---------------------  ----------------
Most Points Scored:    Marco
Least Points Scored:   Ellie
Best Possible Lineup:  Desi
Best Trio:             Desi
Worst Trio:            Vincent
---------------------  ----------------
Best QBs:              Nikki
Best RBs:              Desi
Best WRs:              Nikki
Best TEs:              Isabella
Best Flex:             Julia
Best DST:              Marc
Best K:                Ellie
Best Bench:            Ellie
---------------------  ----------------
Worst QBs:             Desi
Worst RBs:             Ellie
Worst WRs:             Julia
Worst TEs:             Vincent
Worst Flex:            Nikki
Worst DST:             Vincent
Worst K:               Marc
Worst Bench:           Gabriel
```

This package also has its own formula for calculating power rankings each week. 
The computation takes in a team's performance over the entire season (with more weight on the recent weeks), while also accounting for luck.
The power rankings for a given week can be viewed using the 'printPowerRankings' method.
```python
 Week  1 
 Power Index                      Team  Owner
-----------------------------  ------  ----------------
The Adams Family               101.52  Marc Chirico
T.Y. Very Much                 101.24  Desi Pilla
Sony with a Chance              93.02  Isabella Chirico
Good Ole   Christian Boys       79.57  Gabriel S
Home Sweet Mahomes              76.30  Nikki  Pilla
Any Tom, Dick,  Harry Will Do   70.96  Vincent Chirico
The Kamara adds 10 pounds       65.41  Julia Selleck
Can you Diggs this?             64.38  Ellie Knecht
```