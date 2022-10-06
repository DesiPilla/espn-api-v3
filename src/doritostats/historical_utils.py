import pandas as pd
from espn_api.football import League, Team

from .fetch_utils import (
    fetch_league
)

from .analytic_utils import (
    get_best_trio,
    get_lineup_efficiency,
    avg_slot_score,
    sum_bench_points,
    get_top_players,
    get_weekly_finish
)


def is_playoff_game(league: League, matchup, week):
    ''' Accepts a League and Matchup object and determines if the matchup was a playoff game '''

    # False if not playoff time yet
    if week <= league.settings.reg_season_count:
        return False

    # False if a team is on Bye
    if not matchup.away_team:
        return False

    # False if it is a team that did not make the playoffs
    elif matchup.home_team.standing > league.settings.playoff_team_count:
        return False

    # Is it at least 1 week after playoffs began?
    elif (week - 1) > league.settings.reg_season_count:
        last_week_score = matchup.away_team.scores[week-2]
        last_week_opp_score = matchup.away_team.schedule[week-2].scores[week-2]

        # True if team won last week
        if last_week_score > last_week_opp_score:
            return True

        # True if team won last week on a tiebreaker
        elif (last_week_score == last_week_opp_score) and (matchup.away_team.points_for > matchup.away_team.schedule[week-2].points_for):
            return True

        # False if team lost last week
        else:
            return False

    # True if it is the first week of the playoffs
    else:
        return True


class PseudoMatchup():
    ''' A skeleton of the '''

    def __init__(self, home_team, away_team):
        self.home_team = home_team
        self.away_team = away_team

    def __repr__(self):
        return f'Matchup({self.home_team}, {self.away_team})'


def get_stats_by_week(league_id, year, swid, espn_s2):

    # Fetch league for year
    league = fetch_league(league_id=league_id,
                          year=year,
                          swid=swid,
                          espn_s2=espn_s2)

    # Instantiate data frame
    df = pd.DataFrame()

    # Loop through every game in the team's schedule
    for week in range(min(len(league.settings.matchup_periods), league.currentMatchupPeriod)):

        # Instantiate week data frame
        df_week = pd.DataFrame()

        # Loop through every team
        for i, team in enumerate(league.teams):

            # Skip byes
            if team.schedule[i] == team:
                continue

            # Add observation for home team
            df_week.loc[i, 'year'] = year
            df_week.loc[i, 'week'] = week + 1
            df_week.loc[i, 'location'] = team.outcomes[week]
            df_week.loc[i, 'team_owner'] = team.owner
            df_week.loc[i, 'team_name'] = team.team_name
            df_week.loc[i, 'team_division'] = team.division_name
            df_week.loc[i, 'team_score'] = team.scores[week]

            df_week.loc[i, 'opp_owner'] = team.schedule[week].owner
            df_week.loc[i, 'opp_name'] = team.schedule[week].team_name
            df_week.loc[i, 'opp_division'] = team.schedule[week].division_name
            df_week.loc[i, 'opp_score'] = team.schedule[week].scores[week]

            # Is the game in the regular season?
            df_week.loc[i, 'is_regular_season'] = week < league.settings.reg_season_count

            # Is the game a playoff game? (not including consolation)
            # Home team is the lower seed
            matchup_teams = sorted(
                [team, team.schedule[week]], key=lambda x: x.standing)
            matchup = PseudoMatchup(matchup_teams[0], matchup_teams[1])
            df_week.loc[i, 'is_playoff'] = is_playoff_game(
                league, matchup, week+1)

        df = pd.concat([df, df_week])

    # Calculated fields
    df['score_dif'] = df['team_score'] - df['opp_score']

    # Calculated fields
    def calculate_outcome(s):
        if s.score_dif > 0:
            return 'win'
        elif s.score_dif < 0:
            return 'lose'
        else:
            return 'tie'

    df['outcome'] = df.apply(calculate_outcome, axis=1)
    df['is_meaningful_game'] = df.is_regular_season | df.is_playoff

    return df


def get_stats_by_matchup(year):
    # Fetch league for year
    league = fetch_league(league_id=league_id,
                          year=year,
                          swid=swid,
                          espn_s2=espn_s2)

    # Instantiate data frame
    df = pd.DataFrame()

    # Loop through each week that has happened
    for week in range(league.current_week):
        box_scores = league.box_scores(week + 1)

        # Instantiate week data frame
        df_week = pd.DataFrame()
        for i, matchup in enumerate(box_scores):

            # Skip byes
            if (type(matchup.home_team) != Team) or (type(matchup.away_team) != Team):
                continue

            # Add observation for home team
            df_week.loc[i*2, 'year'] = year
            df_week.loc[i*2, 'week'] = week + 1
            df_week.loc[i*2, 'location'] = matchup.home_team.outcomes[week]
            df_week.loc[i*2, 'team_owner'] = matchup.home_team.owner
            df_week.loc[i*2, 'team_name'] = matchup.home_team.team_name
            df_week.loc[i*2, 'team_division'] = matchup.home_team.division_name
            df_week.loc[i*2, 'team_score'] = matchup.home_score
            df_week.loc[i*2, 'opp_owner'] = matchup.away_team.owner
            df_week.loc[i*2, 'opp_name'] = matchup.away_team.team_name
            df_week.loc[i*2, 'opp_division'] = matchup.away_team.division_name
            df_week.loc[i*2, 'opp_score'] = matchup.away_score
            df_week.loc[i*2, 'is_regular_season'] = week < league.settings.reg_season_count
            df_week.loc[i*2,
                        'is_playoff'] = is_playoff_game(league, matchup, week+1)

            home_lineup = matchup.home_lineup
            df_week.loc[i*2, 'weekly_finish'] = get_weekly_finish(
                league, matchup.home_team, week+1)
            df_week.loc[i*2,
                        'lineup_efficiency'] = get_lineup_efficiency(league, home_lineup)
            df_week.loc[i*2, 'best_trio'] = get_best_trio(league, home_lineup)
            df_week.loc[i*2,
                        'bench_points'] = sum_bench_points(league, home_lineup)
            for slot in ['QB', 'RB', 'WR', 'TE', 'RB/WR/TE', 'D/ST', 'K']:
                df_week.loc[i*2, '{}_pts'.format(slot.replace('/', '_'))] = avg_slot_score(
                    league, home_lineup, slot=slot)
                df_week.loc[i*2, 'best_{}'.format(slot.replace('/', '_'))] = get_top_players(
                    home_lineup, slot, 1)[0].points
#                 df_week.loc[i*2, 'worst_{}'.format(slot.replace('/', '_'))] = np.min([player.points for player in get_top_players(home_lineup, slot, 10) if player.slot_position not in ('BE', 'IR')])

            # Add observation for away team
            df_week.loc[i*2+1, 'year'] = year
            df_week.loc[i*2+1, 'week'] = week + 1
            df_week.loc[i*2+1, 'location'] = matchup.away_team.outcomes[week]
            df_week.loc[i*2+1, 'team_owner'] = matchup.away_team.owner
            df_week.loc[i*2+1, 'team_name'] = matchup.away_team.team_name
            df_week.loc[i*2+1, 'team_division'] = matchup.away_team.division_name
            df_week.loc[i*2+1, 'team_score'] = matchup.away_score
            df_week.loc[i*2+1, 'opp_owner'] = matchup.home_team.owner
            df_week.loc[i*2+1, 'opp_name'] = matchup.home_team.team_name
            df_week.loc[i*2+1, 'opp_division'] = matchup.home_team.division_name
            df_week.loc[i*2+1, 'opp_score'] = matchup.home_score
            df_week.loc[i*2+1,
                        'is_regular_season'] = week < league.settings.reg_season_count
            df_week.loc[i*2+1,
                        'is_playoff'] = is_playoff_game(league, matchup, week+1)

            away_lineup = matchup.away_lineup
            df_week.loc[i*2+1, 'weekly_finish'] = get_weekly_finish(
                league, matchup.away_team, week+1)
            df_week.loc[i*2+1,
                        'lineup_efficiency'] = get_lineup_efficiency(league, away_lineup)
            df_week.loc[i*2+1,
                        'best_trio'] = get_best_trio(league, away_lineup)
            df_week.loc[i*2+1,
                        'bench_points'] = sum_bench_points(league, away_lineup)
            for slot in ['QB', 'RB', 'WR', 'TE', 'RB/WR/TE', 'D/ST', 'K']:
                df_week.loc[i*2+1, '{}_pts'.format(slot.replace('/', '_'))] = avg_slot_score(
                    league, away_lineup, slot=slot)
                df_week.loc[i*2+1, 'best_{}'.format(slot.replace('/', '_'))] = get_top_players(
                    away_lineup, slot, 1)[0].points
#                 df_week.loc[i*2+1, 'worst_{}'.format(slot.replace('/', '_'))] = np.min([player.points for player in get_top_players(home_lineup, slot, 10) if player.slot_position not in ('BE', 'IR')])

    #         df_week.loc[i*2, 'team_record'] = "{}-{}-{}".format(matchup.home_team.wins, matchup.home_team.losses, matchup.home_team.ties)
    #         df_week.loc[i*2, 'team_season_points_for'] = matchup.home_team.points_for
    #         df_week.loc[i*2, 'team_season_standing'] = matchup.home_team.standing
    #         df_week.loc[i*2, 'team_season_streak'] = "{}-{}".format(matchup.home_team.streak_type, matchup.home_team.streak_length)
    #         df_week.loc[i*2, 'team_projected'] = matchup.home_projected

        # Concatenate week's data
        df = pd.concat([df, df_week])

    # Calculated fields
    df['score_dif'] = df['team_score'] - df['opp_score']

    # Calculated fields
    def calculate_outcome(s):
        if s.score_dif > 0:
            return 'win'
        elif s.score_dif < 0:
            return 'lose'
        else:
            return 'tie'

    df['outcome'] = df.apply(calculate_outcome, axis=1)
    df['is_meaningful_game'] = df.is_regular_season | df.is_playoff

    return df
