# espn-api-v3

Link to [website](https://doritostats.up.railway.app/)

Link to [Postgres database](https://console.neon.tech/app/projects/spring-star-554438) on Neon

This project aims to make ESPN Fantasy Football statistics easily available.
With the introduction of version 3 of the ESPN's API, this structure creates leagues, teams, and player classes that allow for advanced data analytics and the potential for many new features to be added.

This project was initially inspired by[rbarton65/espnff](https://github.com/rbarton65/espnff)

This project would not be possible without all the amazing work by [cwendt94/ff-espn-api](https://github.com/cwendt94/ff-espn-api)

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

The main website for this project is [here](https://doritostats.up.railway.app/fantasy_stats/). It is a django-based web application, hosted by [Railway](https://railway.app/), and open to the public to use. Go add your own league for the simplest access to stats!

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

```python
week = 4
team_lineup = get_lineup(league, team, week=week)

# Get a team's best possible lineup
get_best_lineup(league, team_lineup)

# Get the total number of TDs scored by a team's starting lineup
get_total_tds(league, team_lineup)

# Get a team's best trio (QB pts + RB pts + WR pts)
get_best_trio(league, team_lineup)

# Get a team's lineup efficiency
get_lineup_efficiency(league, team_lineup)

# Get a team's projection beat
get_score_surprise(league, team_lineup)
```

<a name="powerrankings"></a>

## Power Rankings


```python
>>> league.power_rankings(week)
[('40.15', Team(Buffalo Soldierin')),
 ('38.95', Team(Prendi Un)),
 ('29.50', Team(Tuck Me Into Bed)),
 ('26.55', Team(The  Terrors)),
 ('26.15', Team(Open To Suggestions)),
 ('25.30', Team(Harris Styles)),
 ('24.90', Team(McCaffré: Wins are Brewin)),
 ('24.85', Team(Herbert Hijinks)),
 ('23.05', Team(My Fave Cousin (2 Play Aginst))),
 ('22.40', Team(Zio Cam's Steelers))]
```

<a name="luckindex"></a>

## Luck Index

This package has its own formula for calculating how "lucky" a team has been over the course of a season. Each week, every team is assigned a luck score
based on how they did relative to the rest of the league and the result of their weekly matchup. Teams that performed poorly but still won are assigned
a higher score, while teams that did well but still lost are assigned lower scores. The other determinant in a team's weekly luck score is how well they performed
relative to their average performance, as well as how their opponent performed relative to their average score. Team's who scored exceptionally higher than they
normally do will have a higher luck score, and vice versa. Likewise, team's who face opponents that over-acheive relative to their typical performance will have
a lower (or more 'unlucky') score. Over the course of the season, the luck scores are totaled and the luck index is compiled. 

```python
>>> get_season_luck_indices(league, week)
{Team(Harris Styles): 0.3564328519179781,
 Team(Prendi Un): 1.087036995149442,
 Team(Open To Suggestions): -0.8927507568918904,
 Team(McCaffré: Wins are Brewin): -0.37798381972324224,
 Team(My Fave Cousin (2 Play Aginst)): -0.9647671155447507,
 Team(Tuck Me Into Bed): 0.5335406616193096,
 Team(Buffalo Soldierin'): 0.587489019366005,
 Team(The  Terrors): 0.21217262172352616,
 Team(Zio Cam's Steelers): -0.9233120448553755,
 Team(Herbert Hijinks): -0.1452755616732036}
```

## Historical stats

If a league has been around for more than one season, historical records can be easily fetched. A row will exist for each team's matchup.

```python
from src.doritostats.fetch_utils import get_historical_stats

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
- `team_projection`
- `outcome`
- `is_meaningful_game`
- `season_wins`
- `season_ties`
- `season_losses`
- `win_pct`
- `win_pct_entering_matchup`
- `box_score_available`
- `weekly_finish`
- `lineup_efficiency`
- `best_trio`
- `bench_points`
- `team_projection_beat`
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
- `opp_score_adj`
- `streak`

## Weekly stats analysis

To see if any records were broken during a given week

```python
>>> from src.doritostats.analytic_utils import weekly_stats_analysis

>>> weekly_stats_analysis(records_df, year=2022, week=1)

----------------------------------------------------------------
|                        Week  7 Analysis                      |
----------------------------------------------------------------
League-wide POSITIVE stats
--------------------------
James Selleck had the 3rd highest lineup_efficiency (1.00 pts) in league history


Franchise POSITIVE stats
--------------------------
Carmine Pilla had the 3rd highest score_dif (45.06 pts) in franchise history
Ben Caro had the 1st highest streak (5.00 pts) in franchise history
Carmine Pilla had the 3rd highest streak (1.00 pts) in franchise history


League-wide NEGATIVE stats
--------------------------
Julia Selleck had the 1st lowest QB_pts (-1.80 pts) in league history
James Selleck had the 1st lowest bench_points (0.80 pts) in league history


Franchise NEGATIVE stats
--------------------------
Julia Selleck had the 1st lowest best_trio (37.60 pts) in franchise history
Julia Selleck had the 1st lowest QB_pts (-1.80 pts) in franchise history
Gianna Selleck had the 1st lowest TE_pts (0.00 pts) in franchise history
```

## Season stats analysis

To see the records for a given season

```python
>>> from src.doritostats.analytic_utils import season_stats_analysis

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
