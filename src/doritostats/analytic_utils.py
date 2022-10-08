import numpy as np
from copy import copy
from espn_api.football import League, Team

''' ANALYTIC FUNCTIONS '''
def get_lineup(league: League, team: Team, week: int, box_scores=None):
    ''' Return the lineup of the given team during the given week '''
    # Get the lineup for the team during the specified week
    if box_scores is None:
        box_scores = league.box_scores(week)
    for box_score in box_scores:
        if team == box_score.home_team:
            return box_score.home_lineup
        elif team == box_score.away_team:
            return box_score.away_lineup


def get_top_players(lineup: list, slot: str, n: int):
    ''' Takes a list of players and returns a list of the top n players based on points scored. '''
    # Gather players of the desired position
    eligible_players = []
    for player in lineup:
        if slot in player.eligibleSlots:
            eligible_players.append(player)

    return sorted(eligible_players, key=lambda x: x.points, reverse=True)[:n]


def get_best_lineup(league: League, lineup: list):
    ''' Returns the best possible lineup for team during the loaded week. '''
    # Save full roster
    saved_roster = copy(lineup)

    # Find Best Lineup
    best_lineup = []
    # Get best RB before best RB/WR/TE
    for slot in sorted(league.roster_settings['starting_roster_slots'].keys(), key=len):
        num_players = league.roster_settings['starting_roster_slots'][slot]
        best_players = get_top_players(saved_roster, slot, num_players)
        best_lineup.extend(best_players)

        # Remove selected players from consideration for other slots
        for player in best_players:
            saved_roster.remove(player)

    return np.sum([player.points for player in best_lineup])


def get_best_trio(league: League, lineup: list):
    ''' Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week. '''
    qb = get_top_players(lineup, 'QB', 1)[0].points
    rb = get_top_players(lineup, 'RB', 1)[0].points
    wr = get_top_players(lineup, 'WR', 1)[0].points
    te = get_top_players(lineup, 'TE', 1)[0].points
    best_trio = round(qb + rb + max(wr, te), 2)
    return best_trio


def get_lineup_efficiency(league: League, lineup: list):
    max_score = get_best_lineup(league, lineup)
    real_score = np.sum(
        [player.points for player in lineup if player.slot_position not in ('BE', 'IR')])
    return real_score / max_score


def get_weekly_finish(league: League, team: Team, week: int):
    ''' Returns the rank of a team compared to the rest of the league by points for (for the loaded week) '''
    league_scores = [tm.scores[week-1] for tm in league.teams]
    league_scores = sorted(league_scores, reverse=True)
    return league_scores.index(team.scores[week-1]) + 1


def get_num_out(league: League, lineup: list):
    ''' Returns the (esimated) number of players who did not play for a team for the loaded week (excluding IR slot players). '''
    num_out = 0
    # TODO: write new code based on if player was injured
    return num_out


def avg_slot_score(league: League, lineup: list, slot: str):
    ''' 
    Returns the average score for starting players of a specified slot.
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.mean([player.points for player in lineup if player.slot_position == slot])


def sum_bench_points(league: League, lineup: list):
    ''' 
    Returns the total score for bench players
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    '''
    return np.sum([player.points for player in lineup if player.slot_position == 'BE'])


''' ADVANCED STATS '''
def get_weekly_luck_index(league: League, team: Team, week: int):
    ''' 
    This function returns an index quantifying how 'lucky' a team was in a given week 
    
    Luck index:
        50% probability of playing a team with a lower record
        25% your play compared to previous weeks
        25% opp's play compared to previous weeks
    '''
    opp = team.schedule[week-1]
    num_teams = len(league.teams)

    # Luck Index based on where the team and its opponent finished compared to the rest of the league
    rank = get_weekly_finish(league, team, week)
    opp_rank = get_weekly_finish(league, opp, week)

    if rank < opp_rank:                                # If the team won...
        # Odds of this team playing a team with a higher score than it
        luck_index = 5 * (rank - 1) / (num_teams - 2)
    elif rank > opp_rank:                              # If the team lost or tied...
        # Odds of this team playing a team with a lower score than it
        luck_index = -5 * (num_teams - rank) / (num_teams - 2)

    # If the team tied...
    elif rank < (num_teams / 2):
        # They are only half as unlucky, because tying is not as bad as losing
        luck_index = -2.5 * (num_teams - rank - 1) / (num_teams - 2)
    else:
        # They are only half as lucky, because tying is not as good as winning
        luck_index = 2.5 * (rank - 1) / (num_teams - 2)

    # Update luck index based on how team played compared to normal
    team_score = team.scores[week - 1]
    team_avg = np.mean(team.scores[:week])
    team_std = np.std(team.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (team_score - team_avg) / team_std

        # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        z_norm = z / (3*team_std) * 2.5
        luck_index += z_norm

    # Update luck index based on how opponent played compared to normal
    opp_score = opp.scores[week - 1]
    opp_avg = np.mean(opp.scores[:week])
    opp_std = np.std(opp.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (opp_score - opp_avg) / opp_std

        # Noramlize the z-score so that a performance 3 std dev's away from the mean has an effect of 2 points on the luck index
        z_norm = z / (3*opp_std) * 2.5
        luck_index -= z_norm

    return luck_index / 10


def get_season_luck_indices(league: League, week: int):
    ''' This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week) '''
    luck_indices = {team: 0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, week)
    return luck_indices


def sort_lineups_by_func(league: League, week: int, func, box_scores=None, **kwargs):
    ''' 
    Sorts league teams according to function. 
    Values are sorted ascending. 
    DOES NOT ACCOUNT FOR TIES
    '''
    if box_scores is None:
        box_scores = league.box_scores(week)
    return sorted(league.teams, key=lambda x: func(league, get_lineup(league, x, week, box_scores), **kwargs))
