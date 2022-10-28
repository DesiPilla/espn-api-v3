df = pandas dataframe

# What are the highest scores in a single week?
df[df.is_meaningful_game].sort_values(by='team_score', ascending=False).head(5)
df[df.is_meaningful_game].sort_values(by='team_score_adj', ascending=False).head(5)

# What are the lowest scores in a single week?
df[df.is_meaningful_game].sort_values(by='team_score', ascending=True).head(5)
df[df.is_meaningful_game].sort_values(by='team_score_adj', ascending=True).head(5)

# What are the lowest scores that did not result in a loss?
df[(df.is_meaningful_game) & (df.outcome != 'lose')].sort_values(by='team_score', ascending=True).head(3)
df[(df.is_meaningful_game) & (df.outcome != 'lose')].sort_values(by='team_score_adj', ascending=True).head(3)

# What are the highest scores that did not resulted in a win?
df[(df.is_meaningful_game) & (df.outcome != 'win')].sort_values(by='team_score', ascending=False).head(3)
df[(df.is_meaningful_game) & (df.outcome != 'win')].sort_values(by='team_score_adj', ascending=False).head(3)

# What are the smallest point differentials in a week?
df[(df.is_meaningful_game) & (df.score_dif >= 0)].sort_values(by='score_dif', ascending=True).head(5)

# What are the largest point differentials in a week?
df[(df.is_meaningful_game) & (df.score_dif >= 0)].sort_values(by='score_dif', ascending=False).head(5)

# What is the highest win percentage by a division in a single week?
(df[(df.is_regular_season) & (df.outcome == "win")].groupby(['year', 'week', 'team_division']).count()['outcome'] / df[(df.is_regular_season)].groupby(['year', 'week', 'team_division']).count()['outcome']).fillna(0).sort_values(ascending=False).head(10)

# What is the highest winning percentage by a division in a single season?
(df[(df.is_meaningful_game) & (df.outcome == "win")].groupby(['year', 'team_division']).count()['outcome'] / df[(df.is_meaningful_game)].groupby(['year', 'team_division']).count()['outcome']).sort_values(ascending=False)