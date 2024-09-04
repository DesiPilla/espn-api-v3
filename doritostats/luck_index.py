import numpy as np
from typing import List, Optional
from espn_api.football import League, Team, Player
from doritostats import analytic_utils


def calculate_scheduling_factor(league: League, team: Team, week: int) -> float:
    """Calculates the scheduling luck factor for a team in a given week.

    Winning team's are considered lucky based on the likelihood of them having played a team with a lower score than them.
    Losing team's are considered unlucky based on the likelihood of them having played a team with a higher score than them.
    Luck is halved for teams that tied, as tying is not as good as winning, but not as bad as losing.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        week (int): The week to calculate the scheduling luck factor for

    Returns:
        float: the luck factor for the given team in the given week
    """
    # Get the team's opponent for the given week
    opp = team.schedule[week - 1]

    # Get the rank of the team and its opponent for the given week
    rank = analytic_utils.get_weekly_finish(league, team, week)
    opp_rank = analytic_utils.get_weekly_finish(league, opp, week)
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

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.
    MOVs that are 10% or more of the lower team's score have the maximum effect.

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


def get_performance_vs_projection_factor(lineup: List[Player]) -> float:
    """This function calculates the performance vs projection factor for a team in a given week.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.
    Score surprises that are 25% or more of the team's projected score have the maximum effect.

    Args:
        lineup (List[Player]): A list of ESPN Player objects representing a team's lineup

    Returns:
        float: The performance vs projection factor for the given team in the given week
    """
    score_surprise = analytic_utils.get_score_surprise(None, lineup)

    # TODO: Incorporate total # of starting players that over/underperformed

    # TODO: Find a better way of scaling score surprise. The method below is crude and trash
    # Normalize the MOV to a percentage of the minimum score
    # Clip the normalized MOV to +/- 10% (so that larger score surprises have zero impact on the factor)
    max_pct = 0.25
    score_surprise_norm = np.clip(score_surprise, -max_pct, max_pct) / max_pct

    # Invert the normalized MOV so that smaller MOVs are more impactful on the factor
    factor = (1 * np.sign(score_surprise_norm)) - score_surprise_norm
    return factor


def get_injury_bye_factor(
    lineup: List[Player], max_roster_size: Optional[int] = None
) -> float:
    """This function calculates the injury/bye factor for a team in a given week.

    Args:
        lineup (List[Player]): A list of ESPN Player objects representing a team's lineup
        max_roster_size (Optional[int], optional): The maximum roster size for the league. Defaults to None.

    Returns:
        float: The injury/bye factor for the given team in the given week
    """
    if max_roster_size is None:
        max_roster_size = len(lineup)

    # TODO: Incorporate the strength of a player who was injured or on bye
    # TODO: Account for players who were dropped due to injury
    num_injured = get_num_inactive(lineup)
    num_bye = get_num_bye(lineup)

    # TODO: Find a better way of scaling injury/bye factor. The method below is crude and trash
    return -1 * (num_injured + num_bye) / max_roster_size


# def get_optimal_vs_actual_factor(
#     league: League,
#     team_lineup: List[Player],
#     opp_lineup: List[Player],
#     actual_outcome: str,
# ) -> float:
#     """This function calculates the optimal vs actual factor for a team in a given week.
#
#     Args:
#         league (League): An ESPN League object
#         team_lineup (List[Player]): A list of ESPN Player objects representing a team's lineup
#         opp_lineup (List[Player]): A list of ESPN Player objects representing a team's opponent's lineup
#         actual_outcome (str): The actual outcome of the matchup ('W', 'L', or 'T')
#
#     Returns:
#         float: The performance vs optimal factor for the given team in the given week
#     """
#     # Get the actual score of the team's lineup
#     opp_actual_score = np.sum(
#         [
#             player.points
#             for player in opp_lineup
#             if player.slot_position not in ("BE", "IR")
#         ]
#     )
#
#     # Get the optimal score of the team's lineup
#     optimal_lineup = analytic_utils.get_best_lineup(league, team_lineup)
#     optimal_score = np.sum(
#         [
#             player.points
#             for player in optimal_lineup
#             if player.slot_position not in ("BE", "IR")
#         ]
#     )
#
#     optimal_factor = 0
#     # For teams that lost...
#     if actual_outcome == "L":
#         # If the team would have won if they had played their optimal lineup, they are unlucky
#         if optimal_score > opp_actual_score:
#             optimal_factor -= 1
#
#         # If the team would have tied if they had played their optimal lineup, they are neutral
#         if optimal_score == opp_actual_score:
#             optimal_factor -= 0.5
#
#     # For teams that tied...
#     if actual_outcome == "T":
#         # If the team would have won if they had played their optimal lineup, they are lucky
#         if optimal_score > opp_actual_score:
#             optimal_factor -= 0.5
#
#     # TODO: Find optimal lineup with 1 swap
#     optimal_lineup_1_swap = get_best_lineup(league, team_lineup)  # wrong
#     optimal_1_swap_score = np.sum(
#         [
#             player.points
#             for player in optimal_lineup_1_swap
#             if player.slot_position not in ("BE", "IR")
#         ]
#     )
#
#     optimal_1_swap_factor = 0
#     # For teams that lost...
#     if actual_outcome == "L":
#         # If the team would have won if they had played their optimal lineup, they are unlucky
#         if optimal_1_swap_score > opp_actual_score:
#             optimal_1_swap_factor -= 1
#
#         # If the team would have tied if they had played their optimal lineup, they are neutral
#         if optimal_1_swap_score == opp_actual_score:
#             optimal_1_swap_factor -= 0.5
#
#     # For teams that tied...
#     if actual_outcome == "T":
#         # If the team would have won if they had played their optimal lineup, they are lucky
#         if optimal_1_swap_score > opp_actual_score:
#             optimal_1_swap_factor -= 0.5
#
#     return (optimal_factor + optimal_1_swap_factor) / 2


# def get_optimal_vs_optimal_factor(
#     league: League,
#     team_lineup: List[Player],
#     opp_lineup: List[Player],
#     actual_outcome: str,
# ) -> float:
#     """This function calculates the optimal vs optimal factor for a team in a given week.
#
#     Args:
#         league (League): An ESPN League object
#         team_lineup (List[Player]): A list of ESPN Player objects representing a team's lineup
#         opp_lineup (List[Player]): A list of ESPN Player objects representing a team's opponent's lineup
#         actual_outcome (str): The actual outcome of the matchup ('W', 'L', or 'T')
#
#     Returns:
#         float: The performance vs optimal factor for the given team in the given week
#     """
#     # Get the optimal score of the team's lineup
#     optimal_lineup = get_best_lineup(league, team_lineup)
#     optimal_score = np.sum(
#         [
#             player.points
#             for player in optimal_lineup
#             if player.slot_position not in ("BE", "IR")
#         ]
#     )
#
#     # Get the optimal score of the team's opponent's lineup
#     opp_optimal_lineup = get_best_lineup(league, opp_lineup)
#     opp_optimal_score = np.sum(
#         [
#             player.points
#             for player in opp_optimal_lineup
#             if player.slot_position not in ("BE", "IR")
#         ]
#     )
#
#     factor = 0
#     # For teams that lost...
#     if actual_outcome == "L":
#         # If the team would have won if they had played their optimal lineup, they are unlucky
#         if optimal_score > opp_optimal_score:
#             factor -= 1
#
#         # If the team would have tied if they had played their optimal lineup, they are neutral
#         if optimal_score == opp_optimal_score:
#             factor -= 0.5
#
#     # For teams that tied...
#     if actual_outcome == "T":
#         # If the team would have won if they had played their optimal lineup, they are lucky
#         if optimal_score > opp_optimal_score:
#             factor -= 0.5
#
#     return factor


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
        "performance_vs_projection": 0.20,
        "injuries_byes": 0.20,
        "performance_vs_historical": 0.10,
        "optimal_vs_actual": 0.10,
        "optimal_vs_optimal": 0.10,
        "margin_of_victory": 0.05,
    }

    # Get the team's outcome for the given week
    outcome = team.outcomes[week - 1]

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

    # Get factors for metrics that require the team's lineup
    team_lineup = analytic_utils.get_lineup(league, team, week)
    opp_lineup = analytic_utils.get_lineup(league, opp, week)

    # Calculate the performance vs projection factor
    projection_factor = get_performance_vs_projection_factor(team_lineup)

    # Calculate the injury/bye factor
    # print(league.settings)
    # max_roster_size = (
    #     sum(league.settings["roster_slots"].values())
    #     - league.settings["roster_slots"]["IR"]
    # )
    # injury_bye_factor = get_injury_bye_factor(team_lineup, max_roster_size)

    # # Calculate the performance vs optimal lineup factor
    # optimal_vs_actual_factor = get_optimal_vs_actual_factor(
    #     league, team_lineup, opp_lineup, outcome
    # )
    # opp_optimal_vs_actual_factor = get_optimal_vs_actual_factor(
    #     league, opp_lineup, team_lineup, outcome
    # )
    # optimal_vs_optimal_factor = get_optimal_vs_optimal_factor(
    #     league, team_lineup, opp_lineup, outcome
    # )

    # Combine the factors
    luck_index = (
        factor_weights["scheduling"] * scheduling_factor
        + factor_weights["performance_vs_historical"] * 2 / 3 * team_performance_factor
        + factor_weights["performance_vs_historical"] * 1 / 3 * opp_performance_factor
        + factor_weights["margin_of_victory"] * margin_of_victory_factor
        + factor_weights["performance_vs_projection"] * projection_factor
    #     + factor_weights["injuries_byes"] * injury_bye_factor
    #     + factor_weights["optimal_vs_actual"] * 2 / 3 * optimal_vs_actual_factor
    #     + factor_weights["optimal_vs_actual"] * 1 / 3 * opp_optimal_vs_actual_factor
    #     + factor_weights["optimal_vs_optimal"] * optimal_vs_optimal_factor
    )

    return luck_index