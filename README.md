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

## Fetch privateleagues
By typing your script into the main.py file:
```python
league_id = 1234
year = 2019
username = yourusername@website.com
password = yourPassword
client = Authorize(username, password)
league = League(league_id, year, client.swid, client.espn_s2)
```
