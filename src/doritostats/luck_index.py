import numpy as np
from typing import Dict, List, Optional, Union
from espn_api.football import League, Team, Player
from espn_api.football.box_score import BoxScore
from src.doritostats.analytic_utils import (
    get_best_lineup,
    get_lineup,
    get_num_bye,
    get_num_inactive,
    get_projected_score,
    get_score_surprise,
    get_weekly_finish,
)


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
    team_score: float,
    team_scores: List[float],
) -> float:
    """Calculate the performance of a team in a given week vs their historical average

    The performance is calculated as the z-score of the team's score in the given week
    vs the average of their scores.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.
    Performances that are 2 standard deviations away from the mean have the maximum effect.

    Args:
        team_score (float): The team's score in the given week
        team_scores (List[float]): A list of the team's scores for each week

    Returns:
        float: the luck factor for the given team in the given week
    """
    # Only consider a team's score up to the current week
    team_avg = np.mean(team_scores)
    team_std = np.std(team_scores)

    factor: float = 0.0
    if team_std != 0:
        # Get z-score of the team's performance
        z = (team_score - team_avg) / team_std

        # Noramlize the z-score so that a performance 2 std dev's away from the mean has the
        # maximum effect
        factor += np.clip(z / 2, -1, 1)

    return factor


def calculate_margin_of_victory_factor(team_score: float, opp_score: float) -> float:
    """Calculate the margin of victory factor for a team in a given week.

    The luck factor ranges from -1 to 1, where -1 is the most unlucky and 1 is the most lucky.
    MOVs that are 20% (max_pct) or more of the lower team's score have the maximum effect.

    Args:
        team_score (float): The team's score in the given week
        opp_score (float): The opponent's score in the given week

    Returns:
        float: The luck factor for the team in the given week
    """
    if not (team_score and opp_score):
        return 0

    # Calculate the margin of victory
    mov = team_score - opp_score

    # Normalize the margin of victory by the minimum of the two scores
    # The same denominator is used for both teams so that the sum of the two factors is 0
    # TODO: Find a better way of scaling MOV. The method below is crude and trash

    # Normalize the MOV to a percentage of the minimum score
    # Clip the normalized MOV to +/- 10% (so that larger MOVs have zero impact on the factor)
    max_pct = 0.2
    mov_norm = np.clip(mov / min(team_score, opp_score), -max_pct, max_pct) / max_pct

    # Invert the normalized MOV so that smaller MOVs are more impactful on the factor
    factor = np.sign(mov_norm) - mov_norm
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
    projected_score = get_projected_score(None, lineup)
    score_surprise = get_score_surprise(None, lineup)

    if not projected_score:
        return 0

    # TODO: Incorporate total # of starting players that over/underperformed
    # TODO: Find a better way of scaling score surprise. The method below is crude and trash
    # Clip the normalized score suprise to +/- 25% (so that larger score surprises have higher impact on the factor)
    max_pct = 0.25
    score_surprise_norm = (
        np.clip(score_surprise / projected_score, -max_pct, max_pct) / max_pct
    )
    return score_surprise_norm


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
    num_injured = get_num_inactive(None, lineup)
    num_bye = get_num_bye(None, lineup)

    # TODO: Find a better way of scaling injury/bye factor. The method below is crude and trash
    return -1 * (num_injured + num_bye) / max_roster_size


def get_optimal_vs_actual_factor(
    league: League,
    team_lineup: List[Player],
    opp_lineup: List[Player],
    actual_outcome: str,
) -> float:
    """This function calculates the optimal vs actual factor for a team in a given week.

    Args:
        league (League): An ESPN League object
        team_lineup (List[Player]): A list of ESPN Player objects representing a team's lineup
        opp_lineup (List[Player]): A list of ESPN Player objects representing a team's opponent's lineup
        actual_outcome (str): The actual outcome of the matchup ('W', 'L', or 'T')

    Returns:
        float: The performance vs optimal factor for the given team in the given week
    """
    # Get the actual score of the team's lineup
    opp_actual_score = np.sum(
        [
            player.points
            for player in opp_lineup
            if player.slot_position not in ("BE", "IR")
        ]
    )

    # Get the optimal score of the team's lineup
    optimal_score = get_best_lineup(league, team_lineup)

    optimal_factor = 0
    # For teams that lost...
    if actual_outcome == "L":
        # If the team would have won if they had played their optimal lineup, they are unlucky
        if optimal_score > opp_actual_score:
            optimal_factor -= 1

        # If the team would have tied if they had played their optimal lineup, they are neutral
        if optimal_score == opp_actual_score:
            optimal_factor -= 0.5

    # For teams that tied...
    if actual_outcome == "T":
        # If the team would have won if they had played their optimal lineup, they are lucky
        if optimal_score > opp_actual_score:
            optimal_factor -= 0.5

    return optimal_factor

    # # TODO: Find optimal lineup with 1 swap
    # optimal_1_swap_score = get_best_lineup(league, team_lineup)  # wrong

    # optimal_1_swap_factor = 0
    # # For teams that lost...
    # if actual_outcome == "L":
    #     # If the team would have won if they had played their optimal lineup, they are unlucky
    #     if optimal_1_swap_score > opp_actual_score:
    #         optimal_1_swap_factor -= 1

    #     # If the team would have tied if they had played their optimal lineup, they are neutral
    #     if optimal_1_swap_score == opp_actual_score:
    #         optimal_1_swap_factor -= 0.5

    # # For teams that tied...
    # if actual_outcome == "T":
    #     # If the team would have won if they had played their optimal lineup, they are lucky
    #     if optimal_1_swap_score > opp_actual_score:
    #         optimal_1_swap_factor -= 0.5

    # return (optimal_factor + optimal_1_swap_factor) / 2


def get_optimal_vs_optimal_factor(
    league: League,
    team_lineup: List[Player],
    opp_lineup: List[Player],
    actual_outcome: str,
) -> float:
    """This function calculates the optimal vs optimal factor for a team in a given week.

    Args:
        league (League): An ESPN League object
        team_lineup (List[Player]): A list of ESPN Player objects representing a team's lineup
        opp_lineup (List[Player]): A list of ESPN Player objects representing a team's opponent's lineup
        actual_outcome (str): The actual outcome of the matchup ('W', 'L', or 'T')

    Returns:
        float: The performance vs optimal factor for the given team in the given week
    """
    # Get the optimal score of the team's lineup
    optimal_score = get_best_lineup(league, team_lineup)

    # Get the optimal score of the team's opponent's lineup
    opp_optimal_score = get_best_lineup(league, opp_lineup)

    factor = 0
    # For teams that won...
    if actual_outcome == "W":
        # If the team would have lost if both teams had played their optimal lineup, they are lucky
        if optimal_score < opp_optimal_score:
            factor += 1

        # If the team would have tied if both teams had played their optimal lineup, they are neutral
        if optimal_score == opp_optimal_score:
            factor += 0.5

    # For teams that lost...
    if actual_outcome == "L":
        # If the team would have won if both teams had played their optimal lineup, they are unlucky
        if optimal_score > opp_optimal_score:
            factor -= 1

        # If the team would have tied if both teams had played their optimal lineup, they are neutral
        if optimal_score == opp_optimal_score:
            factor -= 0.5

    # For teams that tied...
    if actual_outcome == "T":
        # If the team would have won if both teams had played their optimal lineup, they are unlucky
        if optimal_score > opp_optimal_score:
            factor -= 0.5

        # If the team would have lost if both teams had played their optimal lineup, they are lucky
        if optimal_score < opp_optimal_score:
            factor += 0.5

    return factor


def get_weekly_luck_index(
    league: League,
    team: Team,
    week: int,
    box_scores: Optional[List[BoxScore]] = None,
    return_factors: bool = False,
) -> Union[float, Dict[str, float]]:
    """This function calculates the weekly luck index for a team in a given week.
    It does so by blending in many different factors.

    Each factor also has a weight adjustment. This is to normalize each factor to have an
    average weight of zero. For example, the factor due to byes & injuries will always be
    negative (if there are any number of byes/injuries) or zero (if there are no byes/injures).
    However, because this is purely a negative factor, it can also be said that having no
    byes/injuries is actually lucky, not neutral.

    Args:
        league (League): An ESPN League object
        team (Team): An ESPN Team object
        week (int): The week to calculate the luck index for
        box_scores (Optional[List[BoxScore]]): A list of ESPN BoxScore objects for the given week. Defaults to None.
        return_factors (bool): Whether to return the individual factors that make up the luck index. Defaults to False.

    Returns:
        float: The luck index for the given team in the given week
        or
        Dict[str, float]: A dictionary of the individual factors that make up the luck index
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
        team.scores[week - 1],
        team.scores,
    )
    opp_performance_factor = calculate_performance_vs_historical_average(
        opp.scores[week - 1],
        opp.scores,
    )

    # Calculate the margin of victory factor
    margin_of_victory_factor = calculate_margin_of_victory_factor(
        team_score=team.scores[week - 1],
        opp_score=opp.scores[week - 1],
    )

    # Get factors for metrics that require the team's lineup
    if box_scores is None:
        box_scores = league.box_scores(week)
    team_lineup = get_lineup(league=league, team=team, week=week, box_scores=box_scores)
    opp_lineup = get_lineup(league=league, team=opp, week=week, box_scores=box_scores)

    # Calculate the performance vs projection factor
    projection_factor = get_performance_vs_projection_factor(team_lineup)

    # Calculate the injury/bye factor
    max_roster_size = sum(
        [
            count
            for slot, count in league.roster_settings["roster_slots"].items()
            if slot != "IR"
        ]
    )
    injury_bye_factor = get_injury_bye_factor(team_lineup, max_roster_size)
    opp_injury_bye_factor = get_injury_bye_factor(opp_lineup, max_roster_size)

    # Calculate the performance vs optimal lineup factor
    optimal_vs_actual_factor = get_optimal_vs_actual_factor(
        league, team_lineup, opp_lineup, outcome
    )
    opp_optimal_vs_actual_factor = get_optimal_vs_actual_factor(
        league, opp_lineup, team_lineup, outcome
    )
    optimal_vs_optimal_factor = get_optimal_vs_optimal_factor(
        league, team_lineup, opp_lineup, outcome
    )

    # Factors skew positive or negative, so an adjustment is needed
    # Injuries/byes factor is week-dependent, as not all weeks have byes
    factor_weight_adjustments = {
        "performance_vs_projection": -0.0140,
        "injuries_byes": {
            1: -0.04821658498574727,
            2: -0.05462462377911275,
            3: -0.07378159473523208,
            4: -0.05988203396348101,
            5: -0.12914084334115997,
            6: -0.13103688629728863,
            7: -0.19256673733397794,
            8: -0.08341519059524279,
            9: -0.18534342059744405,
            10: -0.17147536390054255,
            11: -0.14725777569565657,
            12: -0.07753578793949584,
            13: -0.16768422902890318,
            14: -0.13733533055934166,
            15: -0.08955988712865509,
            16: -0.08746216288440906,
            17: -0.11969066586929249,
            18: -0.1611111111111111,
        },
        "optimal_vs_actual": -0.1872,
        "opp_optimal_vs_actual": -0.4970,
    }
    projection_factor -= factor_weight_adjustments["performance_vs_projection"]
    injury_bye_factor -= factor_weight_adjustments["injuries_byes"][week]
    opp_injury_bye_factor -= factor_weight_adjustments["injuries_byes"][week]
    optimal_vs_actual_factor -= factor_weight_adjustments["optimal_vs_actual"]
    opp_optimal_vs_actual_factor -= factor_weight_adjustments["opp_optimal_vs_actual"]

    # Combine the factors
    luck_index = (
        factor_weights["scheduling"] * scheduling_factor
        + factor_weights["performance_vs_historical"] * 2 / 3 * team_performance_factor
        + factor_weights["performance_vs_historical"] * 1 / 3 * opp_performance_factor
        + factor_weights["margin_of_victory"] * margin_of_victory_factor
        + factor_weights["performance_vs_projection"] * projection_factor
        + factor_weights["injuries_byes"] * 2 / 3 * injury_bye_factor
        + factor_weights["injuries_byes"] * 1 / 3 * opp_injury_bye_factor
        + factor_weights["optimal_vs_actual"] * 2 / 3 * optimal_vs_actual_factor
        + factor_weights["optimal_vs_actual"] * 1 / 3 * opp_optimal_vs_actual_factor
        + factor_weights["optimal_vs_optimal"] * optimal_vs_optimal_factor
    )

    if return_factors:
        return {
            "scheduling": scheduling_factor,
            "performance_vs_historical": team_performance_factor,
            "opp_performance_vs_historical": opp_performance_factor,
            "margin_of_victory": margin_of_victory_factor,
            "performance_vs_projection": projection_factor,
            "injuries_byes": injury_bye_factor,
            "opp_injuries_byes": opp_injury_bye_factor,
            "optimal_vs_actual": optimal_vs_actual_factor,
            "opp_optimal_vs_actual": opp_optimal_vs_actual_factor,
            "optimal_vs_optimal": optimal_vs_optimal_factor,
            "overall_luck_index": luck_index,
        }

    return luck_index


# def old_get_weekly_luck_index(league: League, team: Team, week: int) -> float:
#     """
#     OLD FUNCTION!!!!! NO LONGER USED!!!!!
#     This function returns an index quantifying how 'lucky' a team was in a given week

#     Luck index:
#         70% probability of playing a team with a lower total
#         20% your play compared to previous weeks
#         10% opp's play compared to previous weeks
#     """
#     opp = team.schedule[week - 1]
#     num_teams = len(league.teams)

#     # Set weights
#     w_sched = 7
#     w_team = 2
#     w_opp = 1

#     # Luck Index based on where the team and its opponent finished compared to the rest of the league
#     rank = get_weekly_finish(league, team, week)
#     opp_rank = get_weekly_finish(league, opp, week)

#     if rank < opp_rank:  # If the team won...
#         # Odds of this team playing a team with a higher score than it
#         luck_index = w_sched * (rank - 1) / (num_teams - 1)
#     elif rank > opp_rank:  # If the team lost or tied...
#         # Odds of this team playing a team with a lower score than it
#         luck_index = -w_sched * (num_teams - rank) / (num_teams - 1)

#     # If the team tied...
#     elif rank < (num_teams / 2):
#         # They are only half as unlucky, because tying is not as bad as losing
#         luck_index = -w_sched / 2 * (num_teams - rank - 1) / (num_teams - 1)
#     else:
#         # They are only half as lucky, because tying is not as good as winning
#         luck_index = w_sched / 2 * (rank - 1) / (num_teams - 1)

#     # Update luck index based on how team played compared to normal
#     team_score = team.scores[week - 1]
#     team_avg = np.mean(team.scores[:week])
#     team_std = np.std(team.scores[:week])
#     if team_std != 0:
#         # Get z-score of the team's performance
#         z = (team_score - team_avg) / team_std

#         # Noramlize the z-score so that a performance 2 std dev's away from the mean has an effect of 20% on the luck index
#         z_norm = z / 2 * w_team
#         luck_index += z_norm

#     # Update luck index based on how opponent played compared to normal
#     opp_score = opp.scores[week - 1]
#     opp_avg = np.mean(opp.scores[:week])
#     opp_std = np.std(opp.scores[:week])
#     if team_std != 0:
#         # Get z-score of the team's performance
#         z = (opp_score - opp_avg) / opp_std

#         # Noramlize the z-score so that a performance 2 std dev's away from the mean has an effect of 10% on the luck index
#         z_norm = z / 2 * w_opp
#         luck_index -= z_norm

#     return luck_index / np.sum([w_sched, w_team, w_opp])


def get_season_luck_indices(league: League, week: int) -> Dict[Team, float]:
    """This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week)"""
    luck_indices = {team: 0.0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, wk)

    return luck_indices
