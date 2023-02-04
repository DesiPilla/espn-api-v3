# espn-api-v3

Link to [Railway website](https://doritostats.up.railway.app/)

Link to [Postgres database](https://console.neon.tech/app/projects/spring-star-554438) on Neon

Link to [Heroku website](https://doritostats.herokuapp.com/fantasy_stats/) (WILL BE DEACTIVATED ON NOV 28TH, 2022)

This project aims to make ESPN Fantasy Football statistics easily available.
With the introduction of version 3 of the ESPN's API, this structure creates leagues, teams, and player classes that allow for advanced data analytics and the potential for many new features to be added.

This project was inspired and based off of [rbarton65/espnff](https://github.com/rbarton65/espnff)

Additional help/ideas were received from [cwendt94/ff-espn-api](https://github.com/cwendt94/ff-espn-api)

## Table of Contents

- [Dorito Stats Website](##doritoStatsWebsite)
- Fetching leagues
  - [Fetch public leagues](##fetchpublicleagues)
  - [Fetch private leagues](##fetchprivateleagues)
- Viewing league information
  - [View league information](##viewleagueinformation)
  - [View team information](##viewteaminformation)
  - [View player information](##viewplayerinformation)
  - [View stats for a specific week](##viewstatsforaspecificweek)
- Analytic Methods
  - [Power Rankings](##powerrankings)
  - [Luck Index](##luckindex)
  - [Projected Standings](##projectedstandings)

<a name="doritoStatsWebsite"></a>

## Dorito Stats Website

The main website for this project is [here](https://doritostats.herokuapp.com/fantasy_stats/). It is a django-based web application, hosted by Heroku, and open to the public to use. Go add your own league for the simplest access to stats!

<a name="fetchpublicleagues"></a>

## Fetch public leagues

If your league is public, you don't need any credentials to pull data. The `fetch_league()` function will create a `League` object for your league that is populated with information about your league.

```python
>>> from src.doritostats.fetch_utils import fetch_league
>>> league_id = 1234
>>> year = 2022
>>> league = fetch_league(league_id, year)
[BUILDING LEAGUE] Fetching league data...
[BUILDING LEAGUE] Gathering roster settings information...
[BUILDING LEAGUE] Loading current league details...
```

<a name="fetchprivateleagues"></a>

## Fetch private leagues

If your league is private, you will need to get your `SWID` and `espn_s2` cookies from [espn.com](https://www.espn.com/fantasy/). The `fetch_league()` function will create a `League` object for your league that is populated with information about your league.

```python
>>> league_id = 1234
>>> year      = 2020
>>> swid      = "55B70875-3AS..."
>>> espn_s2   = "AEApIq..."
>>>
>>> league = fetch_league(league_id, year, swid, espn_s2)
[BUILDING LEAGUE] Fetching league data...
[BUILDING LEAGUE] Gathering roster settings information...
[BUILDING LEAGUE] Loading current league details...
```

<a name="viewleagueinformation"></a>

## View league information

You can view high level information about a league using the [`League`](https://github.com/cwendt94/espn-api/blob/3bffd8b5f2fee3360c1a039221f9f5fedc127ac5/espn_api/football/league.py#L17) object returned by `fetch_league`. Info that can be found includes:

```python
>>> league.name
'La Lega dei Cugini'
>>> league.year
2022
>>> league.current_week
8
```

To get details about the league's settings, there is a [`Settings`](https://github.com/cwendt94/espn-api/blob/3bffd8b5f2fee3360c1a039221f9f5fedc127ac5/espn_api/base_settings.py#L1) object. Info that can be found includes:

```python
>>> league.settings
Settings(La Lega dei Cugini)
>>> league.settings.reg_season_count
14
>>> league.settings.team_count
10
>>> league.settings.playoff_team_count
6
>>> league.settings.team_count
10
>>> datetime.datetime.fromtimestamp(league.settings.trade_deadline / 1000).ctime()
'Wed Nov 30 12:00:00 2022'
>>> league.settings.division_map
{0: 'East division', 1: 'West division'}
```

<a name="viewteaminformation"></a>

## View team information

```python
>>> league.teams
[Team(Harris Styles),
 Team(Dakstreet Boys),
 Team(Tuck Me Into Bed),
 ...
]

>>> team = league.teams[1]
Team(Harris Styles)
>>> team.owner
'Desi Pilla'
>>> (team.team_name, team.abbrev)
('Harris Styles', 'HS')
>>> (team.division_id, team.division_name)
(0, 'East division)
>>> (team.wins, team.losses, team.ties)
(5, 2, 0)
>>> team.schedule
[Team(Herbert Hijinks),          # Week 1 opponent
 Team(The Return of The Quads),  # Week 2 opponent
 Team(Dakstreet Boys),           # Week 3 opponent
 ...
]
>>> team.scores
[105.5, 118.86, 123.06, ... ]
>>> team.outcomes
['L', 'W', 'W', ... ]
>>> (team.points_for, team.points_against)
(804, 689)
>>>( team.acquisitions, team.drops, team.trades)
(15, 15, 3)
>>> team.playoff_pct
82.5
>>> (team.streak_length, team.streak_type)
(3, 'WIN')
```

`team.roster` contains a list of [`Player`](https://github.com/cwendt94/espn-api/blob/3bffd8b5f2fee3360c1a039221f9f5fedc127ac5/espn_api/football/player.py#L4) objects for each player on the team's roster for the current week.

```python
>>> team.roster
[Player(Najee Harris),
 Player(Travis Kelce),
 Player(Keenan Allen),
 Player(Travis Etienne Jr.),
 ...
]
```

<a name="viewplayerinformation"></a>

## View player information

Here are some of the player details available:

```python
>>> player = team.roster[0]
>>> (player.name, player.proTeam, player.playerId)
('Najee Harris', 'PIT', 4241457)
>>> player.eligibleSlots	# position slot ids that the player can be placed in
['RB', 'RB/WR', 'RB/WR/TE', 'OP', 'BE', 'IR']
>>> player.acquisitionType
"DRAFT"
>>> player.positionId		# position slot id that the user used him in
'RB'
```

There are many specific scoring stats that can be found under `player.stats` for each week.

<a name="viewstatsforaspecificweek"></a>

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

<a name="powerrankings"></a>

## Power Rankings

This package has its own formula for calculating power rankings each week.
The computation takes in a team's performance over the entire season (with more weight on the recent weeks), while also accounting for luck.
The power rankings for a given week can be viewed using the `printPowerRankings` method.

```python
>>> league.printPowerRankings(1)
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

<a name="luckindex"></a>

## Luck Index

This package has its own formula for calculating how "lucky" a team has been over the course of a season. Each week, every team is assigned a luck score
based on how they did relative to the rest of the league and the result of their weekly matchup. Teams that performed poorly but still won are assigned
a higher score, while teams that did well but still lost are assigned lower scores. The other determinant in a team's weekly luck score is how well they performed
relative to their average performance, as well as how their opponent performed relative to their average score. Team's who scored exceptionally higher than they
normally do will have a higher luck score, and vice versa. Likewise, team's who face opponents that over-acheive relative to their typical performance will have
a lower (or more 'unlucky') score. Over the course of the season, the luck scores are totaled and the luck index is compiled. The luck index can be viewed using
the `printLuckIndex` method.

```python
>>> league.printLuckIndex(2)
Through Week 2
 Team                         Luck Index  Owner
-------------------------  ------------  ----------------
Can you Diggs this?                4.29  Ellie Knecht
Sony with a Chance                 2.14  Isabella Chirico
T.Y. Very Much                     0.71  Desi Pilla
The Adams Family                   0     Marc Chirico
Good Ole   Christian Boys          0     Gabriel S
Home Sweet Mahomes                -1.43  Nikki  Pilla
The Kamara adds 10 pounds         -2.14  Julia Selleck
All Tom No Jerry                  -3.57  Vincent Chirico
```

## Projected Standings

Using the power rankings calculated by this package, projections for the final standings can be calculated. The `printExpectedStandings` method can be called to
view the expected standings based on the power rankings through a certain week. The current standings are found, and results of the following matchups are predicted.
For example, if week 2 has just concluded, the most up-to-date projections can be viewed as follows:

```python
>>> league.printExpectedStandings(2)
Week 2
 Team                         Wins    Losses    Ties  Owner
-------------------------  ------  --------  ------  ----------------
T.Y. Very Much                 12         0       0  Desi Pilla
Sony with a Chance             11         1       0  Isabella Chirico
Home Sweet Mahomes              8         4       0  Nikki  Pilla
The Adams Family                6         6       0  Marc Chirico
Good Ole   Christian Boys       5         7       0  Gabriel S
All Tom No Jerry                3         9       0  Vincent Chirico
Can you Diggs this?             3         9       0  Ellie Knecht
The Kamara adds 10 pounds       0        12       0  Julia Selleck

*These standings do not account for tiesbreakers
```

## Historical stats

If a league has been around for more than one season, historical records can be easily fetched. A row will exist for each team's matchup.

```python
from doritostats.fetch_utils import get_historical_stats

historical_df = get_historical_stats(league_id, start_year, end_year, swid, espn_s2)
```

The list of fields available for each record includes:

- `year`
- `week`
- `location`
- `team_owner`
- `team_name`
- `team_division`
- `team_score`
- `opp_owner`
- `opp_name`
- `opp_division`
- `opp_score`
- `is_regular_season`
- `is_playoff`
- `score_dif`
- `outcome`
- `is_meaningful_game`
- `box_score_available`
- `weekly_finish`
- `lineup_efficiency`
- `best_trio`
- `bench_points`
- `QB_pts`
- `best_QB`
- `RB_pts`
- `best_RB`
- `WR_pts`
- `best_WR`
- `TE_pts`
- `best_TE`
- `RB_WR_TE_pts`
- `best_RB_WR_TE`
- `D_ST_pts`
- `best_D_ST`
- `K_pts`
- `best_K`
- `team_score_adj`
- `streak`

## Weekly stats analysis

To see if any records were broken during a given week

```python
>>> from doritostats.analytic_utils import weekly_stats_analysis

>>> weekly_stats_analysis(records_df, year=2022, week=1)

----------------------------------------------------------------
|                        Week  1 Analysis                      |
----------------------------------------------------------------
Carmine Pilla had the 5th highest D_ST_pts (25.0 pts) in league history
Marc Chirico had the 1st lowest TE_pts (0.0 pts) in league history
```

## Season stats analysis

To see the records for a given season

```python
>>> from doritostats.analytic_utils import season_stats_analysis

>>> season_stats_analysis(league, records_df)

----------------------------------------------------------------
|             Season 2022 Analysis (through Week  6)           |
----------------------------------------------------------------
Most wins this season              - 6 wins - Julia Selleck
Highest single game score          - 160 pts - Julia Selleck
Highest average points this season - 133 pts/gm - Julia Selleck
Longest active win streak          - 6 gms - Julia Selleck
Longest win streak this season     - 6 gms - Julia Selleck

Most losses this season           - 5 losses - Carmine Pilla
Lowest single game score          - 66 pts - James Selleck
Lowest average points this season - 108 pts/gm - Carmine Pilla
Longest active loss streak        - -5 gms - Carmine Pilla
Longest loss streak this season   - -5 gms - Carmine Pilla

Most QB pts this season           - 173 pts - Vincent Chirico
Most RB pts this season           - 98 pts - Ben Caro
Most WR pts this season           - 97 pts - Marc Chirico
Most TE pts this season           - 110 pts - Desi Pilla
Most RB/WR/TE pts this season     - 82 pts - Julia Selleck
Most D/ST pts this season         - 72 pts - Vincent Chirico
Most K pts this season            - 66 pts - Gianna Selleck

Fewest QB pts this season         - 83 pts - James Selleck
Fewest RB pts this season         - 52 pts - Gianna Selleck
Fewest WR pts this season         - 48 pts - Ben Caro
Fewest TE pts this season         - 12 pts - Marc Chirico
Fewest RB/WR/TE pts this season   - 38 pts - Carmine Pilla
Fewest D/ST pts this season       - 25 pts - Nikki  Pilla
Fewest K pts this season          - 20 pts - Marc Chirico
```
