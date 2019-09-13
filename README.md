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
>>> player.positionId	# position slot id that the user used him in
2
>>> player.isStarting
True
```