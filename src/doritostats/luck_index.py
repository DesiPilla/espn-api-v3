import numpy as np
from espn_api.football import League, Team
from src.doritostats.analytic_utils import get_weekly_finish


def calculate_scheduling_factor(league: League, team: Team, week: int) -> float:
    """Calculates the scheduling luck factor for a team in a given week.

    Winning team's are considered lucky based on the likelihood of them having played a team with a lower score than them.
    Losing team's are considered unlucky based on the likelihood of them having played a team with a higher score than them.
    Luck is halved for teams that tied, as tying is not as good as winning, but not as bad as losing.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        weel (int): The week to calculate the scheduling luck factor for

    Returns:
        float: the luck factor for the given team in the given week
    """
    # Get the team's opponent for the given week
    opp = team.schedule[week - 1]

    # Get the rank of the team and its opponent for the given week
    rank = get_weekly_finish(league, team, week)
    opp_rank = get_weekly_finish(league, opp, week)
    num_teams = len(league.teams)

    if rank < opp_rank:  # If the team won...
        # Odds of this team playing a team with a higher score than it
        luck_index = (rank - 1) / (num_teams - 1)
    elif rank > opp_rank:  # If the team lost or tied...
        # Odds of this team playing a team with a lower score than it
        luck_index = -1 * (num_teams - rank) / (num_teams - 1)

    # If the team tied...
    elif rank < (num_teams / 2):
        # They are only half as unlucky, because tying is not as bad as losing
        luck_index = -1 / 2 * (num_teams - rank - 1) / (num_teams - 1)
    else:
        # They are only half as lucky, because tying is not as good as winning
        luck_index = 1 / 2 * (rank - 1) / (num_teams - 1)

    return luck_index


def calculate_performance_vs_historical_average(
    league: League, team: Team, week: int
) -> float:
    """Calculate the performance of a team in a given week vs their historical average

    The performance is calculated as the z-score of the team's score in the given week
    vs the average of their scores.

    Future week's are considered in the calculation. This means that a team's weekly luck score
    will change as the season progresses. This is intentional, as it is not known early in the
    season if a team's performance is strong or weak relative to it's true strength. This also
    allows for a more stable factor overall.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.
    Performances that are 2 standard deviations away from the mean have the maximum effect.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        weel (int): The week to calculate the scheduling luck factor for

    Returns:
        float: the luck factor for the given team in the given week
    """
    team_score = team.scores[week - 1]

    # # Only consider a team's score up to the current week
    # team_avg = np.mean(team.scores[:week])
    # team_std = np.std(team.scores[:week])

    # Consider all of a team's scores, even those in future weeks
    team_avg = np.mean(team.scores)
    team_std = np.std(team.scores)

    factor = 0
    if team_std != 0:
        # Get z-score of the team's performance
        z = (team_score - team_avg) / team_std

        # Noramlize the z-score so that a performance 2 std dev's away from the mean has the
        # maximum effect
        factor += np.clip(z / 2, -1, 1)

    return factor


def calculate_margin_of_victory_factor(league: League, team: Team, week: int) -> float:
    """Calculate the margin of victory factor for a team in a given week.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        weel (int): The week to calculate the scheduling luck factor for

    Returns:
        float: The luck factor for the team in the given week
    """
    # Get the team's score and the opponent's score
    team_score = team.scores[week - 1]
    opp_score = team.schedule[week - 1].scores[week - 1]

    team_score = 100
    opp_score = 105

    # Calculate the margin of victory
    mov = team_score - opp_score

    # Normalize the margin of victory by the minimum of the two scores
    # The same denominator is used for both teams so that the sum of the two factors is 0
    # TODO: Find a better way of scaling MOV. The method below is crude and trash

    # Normalize the MOV to a percentage of the minimum score
    # Clip the normalized MOV to +/- 10% (so that larger MOVs have zero impact on the factor)
    max_pct = 0.1
    mov_norm = np.clip(mov / min(team_score, opp_score), -max_pct, max_pct) / max_pct

    # Invert the normalized MOV so that smaller MOVs are more impactful on the factor
    factor = (1 * np.sign(mov_norm)) - mov_norm
    return factor


def get_weekly_luck_index(league: League, team: Team, week: int) -> float:
    """This function calculates the weekly luck index for a team in a given week.
    It does so by blending in many different factors.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        week (int): The week to calculate the luck index for

    Returns:
        float: The luck index for the given team in the given week
    """
    # Define the weights to apply to each factor
    factor_weights = {
        "scheduling": 0.25,
        "projection": 0.20,
        "injuries_byes": 0.20,
        "performance": 0.10,
        "optimal_vs_actual": 0.10,
        "optimal_vs_optimal": 0.10,
        "margin_of_victory": 0.05,
    }

    #  Get the team's opponent for the given week
    opp = team.schedule[week - 1]

    # Calculate the scheduling factor
    scheduling_factor = calculate_scheduling_factor(league, team, week)

    # Calculate the performance factors
    team_performance_factor = calculate_performance_vs_historical_average(
        league, team, week
    )
    opp_performance_factor = calculate_performance_vs_historical_average(
        league, opp, week
    )

    # Calculate the margin of victory factor
    margin_of_victory_factor = calculate_margin_of_victory_factor(league, team, week)

    # Combine the factors
    luck_index = (
        factor_weights["scheduling"] * scheduling_factor
        + factor_weights["performance"] * 2 / 3 * team_performance_factor
        + factor_weights["performance"] * 1 / 3 * opp_performance_factor
        + factor_weights["margin_of_victory"] * margin_of_victory_factor
    )

    return luck_index
