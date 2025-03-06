import numpy as np
import pandas as pd
from copy import copy
from typing import Callable, Dict, List, Optional, Tuple, Union
from espn_api.football import League, Team, Player
from espn_api.football.box_score import BoxScore
from sklearn import preprocessing
from src.doritostats.filter_utils import get_any_records, exclude_most_recent_week


def get_lineup(
    league: League, team: Team, week: int, box_scores: Optional[List[BoxScore]] = None
) -> List[Player]:
    """Return the lineup of the given team during the given week"""
    # Get the lineup for the team during the specified week
    if box_scores is None:
        box_scores = league.box_scores(week)

    assert box_scores is not None

    lineup = []
    for box_score in box_scores:
        if team == box_score.home_team:
            lineup = box_score.home_lineup
        elif team == box_score.away_team:
            lineup = box_score.away_lineup
    return lineup


def get_top_players(lineup: List[Player], slot: str, n: int) -> List[Player]:
    """Takes a list of players and returns a list of the top n players based on points scored."""
    # Gather players of the desired position
    eligible_players = []
    for player in lineup:
        if slot in player.eligibleSlots:
            eligible_players.append(player)
            continue
        if ("TE" in slot) and (player.name == "Taysom Hill"):
            eligible_players.append(player)

    return sorted(eligible_players, key=lambda x: x.points, reverse=True)[:n]


def get_best_lineup(league: League, lineup: List[Player]) -> float:
    """Returns the score of the best possible lineup for team during the loaded week."""
    # Save full roster
    saved_roster = copy(lineup)

    # Find Best Lineup
    best_lineup = []
    # Get best RB before best RB/WR/TE
    for slot in sorted(league.roster_settings["starting_roster_slots"].keys(), key=len):
        num_players = league.roster_settings["starting_roster_slots"][slot]
        best_players = get_top_players(saved_roster, slot, num_players)
        best_lineup.extend(best_players)

        # Remove selected players from consideration for other slots
        for player in best_players:
            saved_roster.remove(player)

    return np.sum([player.points for player in best_lineup])


def get_best_trio(league: League, lineup: List[Player]) -> float:
    """Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week."""
    if "QB" in league.roster_settings["roster_slots"].keys():
        # Most leagues have a QB slot
        qb = get_top_players(lineup, "QB", 1)[0].points
    elif "TQB" in league.roster_settings["roster_slots"].keys():
        # Some leagues use Team QB instead of individual QBs
        qb = get_top_players(lineup, "TQB", 1)[0].points
    else:
        # If for some reason a league doesn't have a QB slot, set it to 0
        qb = 0

    rb = get_top_players(lineup, "RB", 1)[0].points
    wr = get_top_players(lineup, "WR", 1)[0].points

    if "TE" in league.roster_settings["roster_slots"].keys():
        te = get_top_players(lineup, "TE", 1)[0].points
    else:
        # If for some reason a league doesn't have a TE slot, set it to 0
        te = 0
    best_trio = round(qb + rb + max(wr, te), 2)
    return best_trio


def get_lineup_efficiency(league: League, lineup: List[Player]) -> float:
    """
    Returns the lineup efficiency of a team.
    Lineup efficiency is defined as the team's actual score divided by it's best possible score.
    """
    max_score = get_best_lineup(league, lineup)
    real_score = np.sum(
        [player.points for player in lineup if player.slot_position not in ("BE", "IR")]
    )
    return real_score / max_score


def get_weekly_finish(league: League, team: Team, week: int) -> int:
    """Returns the rank of a team compared to the rest of the league by points for (for the loaded week)"""
    league_scores = [tm.scores[week - 1] for tm in league.teams]
    league_scores = sorted(league_scores, reverse=True)
    return league_scores.index(team.scores[week - 1]) + 1


def get_num_active(league: League, lineup: List[Player]) -> int:
    """Returns the number of players who were active for a team for the loaded week (excluding IR slot players)."""
    return len(
        [
            player
            for player in lineup
            if player.active_status == "active" and player.slot_position != "IR"
        ]
    )


def get_num_inactive(league: League, lineup: List[Player]) -> int:
    """Returns the number of players who did not play for a team for the loaded week (excluding IR slot players)."""
    return len(
        [
            player
            for player in lineup
            if player.active_status == "inactive" and player.slot_position != "IR"
        ]
    )


def get_num_bye(league: League, lineup: List[Player]) -> int:
    """Returns the number of players who were on a bye for the loaded week (excluding IR slot players)."""
    return len(
        [
            player
            for player in lineup
            if player.active_status == "bye" and player.slot_position != "IR"
        ]
    )


def avg_slot_score(league: League, lineup: List[Player], slot: str) -> float:
    """
    Returns the average score for starting players of a specified slot.
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    """
    return np.mean([player.points for player in lineup if player.slot_position == slot])  # type: ignore


def sum_bench_points(league: League, lineup: list) -> float:
    """
    Returns the total score for bench players
    `lineup` is either BoxScore().away_lineup or BoxScore().home_lineup (a list of BoxPlayers)
    """
    return np.sum([player.points for player in lineup if player.slot_position == "BE"])


def get_projected_score(league: League, lineup: List[Player]) -> float:
    """
    Returns the projected score of a team's starting lineup.
    """
    return np.sum(
        [
            player.projected_points
            for player in lineup
            if player.slot_position not in ("BE", "IR")
        ]
    )


def get_score_surprise(league: League, lineup: List[Player]) -> float:
    """
    Returns the difference ("surprise") between a team's projected starting score and its actual score.
    """
    projected_score = get_projected_score(league, lineup)
    actual_score = np.sum(
        [player.points for player in lineup if player.slot_position not in ("BE", "IR")]
    )
    return actual_score - projected_score


def get_total_tds(league: League, lineup: List[Player]) -> float:
    """
    Returns the total number of TDs scored by the starting roster.
    """
    total_tds = 0
    for player in lineup:
        # Skip non-starting players
        if player.slot_position in ("BE", "IR"):
            continue

        # Skip players with no stats (players on Bye)
        if not list(player.stats.keys()):
            continue

        player_tds = 0
        for statId in [
            "passingTouchdowns",
            "rushingTouchdowns",
            "receivingTouchdowns",
            "defensiveBlockedKickForTouchdowns",
            "defensiveTouchdowns",
            "kickoffReturnTouchdowns",
            "puntReturnTouchdowns",
            "interceptionReturnTouchdowns",
            "fumbleReturnTouchdowns",
            "defensivePlusSpecialTeamsTouchdowns",
        ]:
            week = list(player.stats.keys())[0]
            if "breakdown" in player.stats[week].keys():
                if statId in player.stats[week]["breakdown"].keys():
                    player_tds += player.stats[week]["breakdown"][statId]
        total_tds += player_tds

    return total_tds


""" ADVANCED STATS """


def calculate_win_pct(outcomes: np.array) -> float:
    """This function returns the win percentage of a team (excluding ties).

    Args:
        outcomes (np.array): Array of outcomes ('W', 'L', 'T')

    Returns:
        float: Win percentage
    """
    if not len(outcomes):
        return 0
    return sum(outcomes == "W") / sum((outcomes == "W") | (outcomes == "L"))


def get_remaining_schedule_difficulty(
    team: Team,
    week: int,
    regular_season_length: int,
    strength: str = "points_for",
    league: Optional[League] = None,
) -> Tuple[float, Tuple[int, int], Tuple[int, int]]:
    """
    This function returns the average score of a team's remaining opponents.

    The `strength` parameter defines how an opponent's "strength" is defined.
        - "points_for" means that difficulty is defined by the average points for scored by each of their remaining opponents.
        - "win_pct" means that the difficult is defined by the average winning percentage of each of their remaining opponents.
        - "power_rank" means that the difficult is defined by the average power rank of each of their remaining opponents.

    Returns:
        float: strength of schedule, as defined by the `strength` parameter
        Tuple[int, int]: Tuple containing the range of weeks included in calculating a team's opponent's strength
            * For example, if the SOS for Week 6 and beyond is desired, this tuple would be (1, 5)
        Tuple[int, int]: Tuple containing the range of weeks defining a team's remaining schedule
            * For example, if the SOS for Week 6 and beyond is desired, this tuple would be (6, regular_season_length)

    """
    if week >= regular_season_length:
        return 0, (0, 0), (0, 0)

    # Get the remaining schedule for the team
    remaining_schedule = team.schedule[week:regular_season_length]
    n_completed_weeks = len(
        [o for o in team.outcomes[:regular_season_length] if o != "U"]
    )

    # How many completed weeks should be included?
    strength_weeks_to_consider = min(week, n_completed_weeks)

    if strength_weeks_to_consider == 0:
        return 0, (0, 0), (0, 0)

    # Define the week ranges for calculating the strength of schedule
    strength_period = (1, strength_weeks_to_consider)
    schedule_period = (
        regular_season_length - len(remaining_schedule) + 1,
        regular_season_length,
    )

    if strength == "points_for":
        # Get all scores from remaining opponents through specified week
        remaining_strength = np.array(
            [opp.scores[:strength_weeks_to_consider] for opp in remaining_schedule]
        ).flatten()

        # # Slower, but easier for dubugging
        # remaining_strength = pd.DataFrame(
        #     [opp.scores[:strength_weeks_to_consider] for opp in remaining_schedule],
        #     columns=[
        #         "Week {} score".format(i)
        #         for i in range(1, strength_weeks_to_consider + 1)
        #     ],
        #     index=[
        #         "Week {} opponent - {}".format(
        #             regular_season_length - len(remaining_schedule) + i + 1, opp.owner
        #         )
        #         for i, opp in enumerate(remaining_schedule)
        #     ],
        # )
        # return (remaining_strength, strength_period, schedule_period)

        # Return average score and calculation periods
        return (remaining_strength.mean(), strength_period, schedule_period)

    elif strength == "win_pct":
        # Get win pct of remaining opponents through specified week
        remaining_strength = np.array(
            [opp.outcomes[:strength_weeks_to_consider] for opp in remaining_schedule]
        ).flatten()

        # # Slower, but easier for dubugging
        # remaining_strength = pd.DataFrame(
        #     [
        #         calculate_win_pct(np.array(opp.outcomes[:strength_weeks_to_consider]))
        #         for opp in remaining_schedule
        #     ],
        #     columns=["Win pct"],
        #     index=[
        #         "Week {} opponent - {}".format(
        #             regular_season_length - len(remaining_schedule) + i + 1, opp.owner
        #         )
        #         for i, opp in enumerate(remaining_schedule)
        #     ],
        # )
        # return (remaining_strength, strength_period, schedule_period)

        # Return average win pct and calculation periods
        return (calculate_win_pct(remaining_strength), strength_period, schedule_period)

    elif strength == "power_rank":
        # Get the power ranking from remaining opponents through specified week
        power_rankings = {
            t: float(r)
            for r, t in league.power_rankings(week=strength_weeks_to_consider)
        }

        remaining_strength = np.array(
            [power_rankings[opp] for opp in remaining_schedule]
        ).flatten()

        # # Slower, but easier for dubugging
        # remaining_strength = pd.DataFrame(
        #     [power_rankings[opp] for opp in remaining_schedule],
        #     columns=["Power rank"],
        #     index=[
        #         "Week {} opponent - {}".format(
        #             regular_season_length - len(remaining_schedule) + i + 1, opp.owner
        #         )
        #         for i, opp in enumerate(remaining_schedule)
        #     ],
        # )
        # return (remaining_strength, strength_period, schedule_period)

        # Return average power rank and calculation periods
        return (remaining_strength.mean(), strength_period, schedule_period)

    else:
        raise Exception("Unrecognized parameter passed for `strength`")


def get_remaining_schedule_difficulty_df(
    league: League, week: int
) -> Tuple[pd.DataFrame, Tuple[int, int], Tuple[int, int]]:
    """
    This function creates a dataframe containing each team's remaining strength of schedule. Strength of schedule is determined by two factors:
        - "opp_points_for" is the average points for scored by each of a team's remaining opponents.
        - "opp_win_pct" is the average winning percentage of each of a team's remaining opponents.
        - "opp_power_rank" is the average power rank of each of a team's remaining opponents.

    Higher SOS values indicate a more difficult remaining schedule.

    Args:
        league (League): League
        week (int): First week to include as "remaining". I.e., week = 10 will calculate the remaining SOS for Weeks 10 -> end of season.

    Returns:
        pd.DataFrame: Dataframe containing the each team's remaining strength of schedule
        Tuple[int, int]: Tuple containing the range of weeks included in calculating a team's opponent's strength
            * For example, if the SOS for Week 6 and beyond is desired, this tuple would be (1, 5)
        Tuple[int, int]: Tuple containing the range of weeks defining a team's remaining schedule
            * For example, if the SOS for Week 6 and beyond is desired, this tuple would be (6, regular_season_length)
    """
    if (week < 1) or league.current_week < 2:
        return pd.DataFrame(
            {
                team: {
                    "opp_points_for": 0,
                    "opp_win_pct": 0,
                    "opp_power_rank": 0,
                    "overall_difficulty": 0,
                }
                for team in league.teams
            }
        ).T

    remaining_difficulty_dict = {}  # type: ignore

    # Get the remaining SOS for each team
    for team in league.teams:
        remaining_difficulty_dict[team] = {}

        # SOS by points for
        (
            remaining_difficulty_dict[team]["opp_points_for"],
            strength_period,
            schedule_period,
        ) = get_remaining_schedule_difficulty(
            team,
            week,
            regular_season_length=league.settings.reg_season_count,
            strength="points_for",
        )  # type: ignore

        # SOS by win pct
        (
            remaining_difficulty_dict[team]["opp_win_pct"],
            _,
            _,
        ) = get_remaining_schedule_difficulty(
            team,
            week,
            regular_season_length=league.settings.reg_season_count,
            strength="win_pct",
        )  # type: ignore

        # SOS by win pct
        (
            remaining_difficulty_dict[team]["opp_power_rank"],
            _,
            _,
        ) = get_remaining_schedule_difficulty(
            team,
            week,
            regular_season_length=league.settings.reg_season_count,
            strength="power_rank",
            league=league,
        )  # type: ignore

    # Identify the min and max values for each SOS metric
    team_avg_score = [t.points_for / (week - 1) for t in league.teams]
    team_win_pct = [
        calculate_win_pct(np.array(t.outcomes[:week])) for t in league.teams
    ]
    power_ranks = [float(p) for p, _ in league.power_rankings(week)]

    # Organize into a dataframe and convert SOS values into a rank order
    remaining_difficulty = pd.DataFrame(remaining_difficulty_dict).T
    remaining_difficulty["opp_points_for_index"] = (
        preprocessing.MinMaxScaler((min(team_avg_score), max(team_avg_score)))
        .fit_transform(remaining_difficulty.opp_points_for.values.reshape(-1, 1))
        .flatten()
    )

    remaining_difficulty["opp_win_pct_index"] = (
        preprocessing.MinMaxScaler((min(team_win_pct), max(team_win_pct)))
        .fit_transform(remaining_difficulty.opp_win_pct.values.reshape(-1, 1))
        .flatten()
    )

    remaining_difficulty["opp_power_rank_index"] = (
        preprocessing.MinMaxScaler((min(power_ranks), max(power_ranks)))
        .fit_transform(remaining_difficulty.opp_power_rank.values.reshape(-1, 1))
        .flatten()
    )

    # Blend the three values (based on ranking, not actual value)
    remaining_difficulty["overall_difficulty"] = remaining_difficulty[
        ["opp_points_for_index", "opp_win_pct_index", "opp_power_rank_index"]
    ].mean(axis=1)

    return (
        remaining_difficulty[
            ["opp_points_for", "opp_win_pct", "opp_power_rank", "overall_difficulty"]
        ].sort_values(by="overall_difficulty", ascending=False),
        strength_period,
        schedule_period,
    )


def sort_lineups_by_func(
    league: League, week: int, func, box_scores=None, **kwargs
) -> List[Team]:
    """
    Sorts league teams according to function.
    Values are sorted ascending.
    DOES NOT ACCOUNT FOR TIES
    """
    if box_scores is None:
        box_scores = league.box_scores(week)
    return sorted(
        league.teams,
        key=lambda x: func(league, get_lineup(league, x, week, box_scores), **kwargs),
    )


def get_leader_str(
    stats_list: List[Tuple[str, float]], high_first: bool = True
) -> Tuple[float, str]:
    """Return a list of team owners who have the best stat,
    given a list of teams and stat values.

    Args:
        stats_list (List[Tuple[str, float]]): list of teams and a stat value
          - Ex: [('Team 1', 103.7), ('Team 2', 83.7), ('Team 3', 98.8)]
        high_first (bool, optional): Are higher values better than lower values?. Defaults to True.

    Returns:
        float: The value being sorted
        str: List of team owners with the highest value
    """

    # Sort list
    sorted_stats_list = sorted(stats_list, key=lambda x: x[1], reverse=high_first)

    # Check if there is no tie
    if sorted_stats_list[0][1] != sorted_stats_list[1][1]:
        return sorted_stats_list[0][1], "{}".format(sorted_stats_list[0][0])

    # If there is a tie, return all teams tied for first
    else:
        leaders = [sorted_stats_list[0][0]]
        for i in range(1, len(sorted_stats_list)):
            # If the stat value is the same, add the owner's name to leaders
            if sorted_stats_list[i][1] == sorted_stats_list[i - 1][1]:
                leaders.append(sorted_stats_list[i][0])

            # If not, end the loop
            else:
                break

        # Return the stat value and the leaders string
        return sorted_stats_list[0][1], "{}".format(", ".join(set(leaders)))


def get_naughty_players(lineup: List[Player], week: int) -> List[Player]:
    """This function identifies all players that were started by their owners, but were inactive or on bye.
    The function returns a list of all players that were started by their owners, but were inactive or on bye.

    A player is only considered "naughty" once they have locked (i.e., their matchup has begun) for the week.
    This is to prevent lineups that have not yet been set from being flagged as "naughty".

    Args:
        lineup (List[Player]): A list of players in a team's lineup
        week (int): The week to check for inactive players

    Returns:
        List[Player]: A list of all players that were started by their owners, but were inactive or on bye.
    """
    return [
        player
        for player in lineup
        if player.active_status in ["bye", "inactive"]  # Player was on bye or inactive
        and player.slot_position
        not in ["IR", "BE"]  # Player was in the player's starting lineup
        and "points" in player.stats[week].keys()  # The player is locked for the week
    ]


def get_naughty_list_str(league: League, week: int) -> List[str]:
    """This function identifies all players that were started by their owners, but were inactive or on bye.

    Args:
        league (League): League object
        week (int): The week to check for inactive players

    Returns:
        List[str]: A list of strings that list all players that were started by their owners, but were inactive or on bye.
    """
    naughty_list_str = []
    for team in league.teams:
        lineup = get_lineup(league, team, week)
        naughty_players = get_naughty_players(lineup, week)
        for player in naughty_players:
            naughty_list_str.append(
                "❌ {} started {} ({})".format(
                    team.owner, player.name, player.active_status
                )
            )

    if not naughty_list_str:
        naughty_list_str = ["🎉 No teams started any inactive players!"]

    return naughty_list_str


def make_ordinal(n: int) -> str:
    """
    Convert an integer into its ordinal representation::
        make_ordinal(3)   => '3rd'
        make_ordinal(122) => '122nd'
        make_ordinal(213) => '213th'
    """
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix


def print_records(
    df: pd.DataFrame,
    year: int,
    week: int,
    stat: str,
    stat_units: str,
    high_first: bool = True,
    n: int = 5,
) -> None:
    """Print out any records.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        year (int): Year to check for a record
        week (int): Week to check for a record
        stat (str): The stat of note ('team_score', 'QB_pts', etc.)
        stat_units (str): ('pts', 'pts/gm', etc.)
        high_first (bool): Are higher values better than lower values?. Defaults to True.
        n (int): How far down the record list to check (defaults to 5)
    """
    records_df = get_any_records(
        df=df, year=year, week=week, stat=stat, high_first=high_first, n=n
    )

    # Print out any records
    superlative = "highest" if high_first else "lowest"
    for _, row in records_df.iterrows():
        print(
            "{} had the {} {} {} ({:.2f} {}) in league history".format(
                row.team_owner,
                make_ordinal(row["rank"]),
                superlative,
                stat,
                row[stat],
                stat_units,
            )
        )


def print_franchise_records(
    df: pd.DataFrame,
    year: int,
    week: int,
    stat: str,
    stat_units: str,
    high_first: bool = True,
    n: int = 1,
) -> None:
    """Print out any franchise records.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        year (int): Year to check for a record
        week (int): Week to check for a record
        stat (str): The stat of note ('team_score', 'QB_pts', etc.)
        stat_units (str): ('pts', 'pts/gm', etc.)
        high_first (bool): Are higher values better than lower values?. Defaults to True.
        n (int): How far down the record list to check (defaults to 5)
    """
    # Get a list of all active teams that have been in the league for 2+ years
    current_teams = df[df["year"] == df["year"].max()].team_owner.unique()
    list_of_teams = df.groupby(["team_owner"]).nunique()
    list_of_teams = list_of_teams[
        (list_of_teams.year > 1) & list_of_teams.index.isin(current_teams)
    ].index.tolist()

    for team_owner in list_of_teams:
        # Get all rows for the given team
        team_df = df[df["team_owner"] == team_owner]

        # Get any records for that team
        records_df = get_any_records(
            df=team_df, year=year, week=week, stat=stat, high_first=high_first, n=n
        )

        # Print out any records
        superlative = "highest" if high_first else "lowest"
        for _, row in records_df.iterrows():
            print(
                "{} had the {} {} {} ({:.2f} {}) in franchise history".format(
                    row.team_owner,
                    make_ordinal(row["rank"]),
                    superlative,
                    stat,
                    row[stat],
                    stat_units,
                )
            )


def get_wins_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Get the all time wins leaderboard for the league.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.Series: Ordered leaderboard by career wins
    """
    df = df[(df["outcome"] == "win") & (df["is_meaningful_game"])]
    leaderboard_df = (
        df.groupby("team_owner")["outcome"]
        .count()
        .sort_values(ascending=False)
        .reset_index()
    )
    leaderboard_df.index += 1
    return leaderboard_df


def get_losses_leaderboard(df: pd.DataFrame) -> pd.DataFrame:
    """Get the all time losses leaderboard for the league.

    Args:
        df (pd.DataFrame): Historical stats dataframe

    Returns:
        pd.Series: Ordered leaderboard by career wins
    """
    df = df[(df["outcome"] == "lose") & (df["is_meaningful_game"])]
    leaderboard_df = (
        df.groupby("team_owner")
        .count()["outcome"]
        .sort_values(ascending=False)
        .reset_index()
    )
    leaderboard_df.index += 1
    return leaderboard_df


def leaderboard_change(
    df: pd.DataFrame, leaderboard_func: Callable = get_wins_leaderboard
) -> pd.DataFrame:
    """This function takes a leaderboard function and calculates
    the change of that leaderboard from the previous week to the current week.

    I.e.: If the get_wins_leaderboard() function is passed in,

    The function will rank teams 1 - n from the previous week.
    Then the leaderboard will be updated with the outcomes of the current week.
    The function will return the change of each team.
    If Team A went from being the winningest team to the 2nd-most winningest team, they would have a change of -1.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        leaderboard_func (Callable, optional): A leaderboard function. Defaults to get_wins_leaderboard.

    Returns:
        pd.DataFrame: A dataframe containing the current leaderboard, previousl eaderboard, and the difference
    """

    # Get current leaderboard
    current_leaderboard = leaderboard_func(df).reset_index()

    # Get leaderboard from last week
    last_week_df = exclude_most_recent_week(df)
    last_week_leaderboard = leaderboard_func(last_week_df).reset_index()

    # Merge the leaderboards on 'team_owner'
    leaderboard_change = (
        current_leaderboard.drop(columns=["outcome"])
        .merge(
            last_week_leaderboard.drop(columns=["outcome"]),
            on="team_owner",
            suffixes=("_current", "_last"),
        )
        .set_index("team_owner")
    )

    # Subtract the two weeks to find the change in leaderboard postioning
    leaderboard_change["change"] = (
        leaderboard_change.index_last - leaderboard_change.index_current
    )

    return leaderboard_change


def get_team(
    league: League, team_owner: Optional[str] = None, team_id: Optional[int] = None
) -> Team:
    """Get the Team object corresponding to the team_owner

    Args:
        league (League): League object containing the teams
        team_owner (str): Team owner to get Team object of

    Raises:
        Exception: If the team owner does not have a Team object in the league

    Returns:
        Team: Team object
    """
    assert (team_owner is not None) or (team_id is not None)
    if team_owner is not None:
        for team in league.teams:
            if team.owner == team_owner:
                return team

        raise Exception(f"Owner {team_owner} not in league.")
    else:
        for team in league.teams:
            if team.team_id == team_id:
                return team

        raise Exception(f"Team ID {team_id} not in league.")


def get_division_standings(league: League) -> Dict[str, List[Team]]:
    standings = {}
    for division in league.settings.division_map.values():
        teams = [team for team in league.teams if team.division_name == division]
        standings[division] = sorted(teams, key=lambda x: x.standing)
    return standings


def game_of_the_week_stats(
    league: League, df: pd.DataFrame, owner1: str, owner2: str
) -> None:
    gow_df = df[
        (df["team_owner"] == owner1)
        & (df["opp_owner"] == owner2)
        & (df["is_meaningful_game"])
    ]
    gow_df.sort_values(["year", "week"], ascending=True, inplace=True)

    print(
        "{} has won {} / {} matchups.".format(
            owner1, len(gow_df[gow_df["outcome"] == "win"]), len(gow_df)
        )
    )
    print(
        "{} has won {} / {} matchups.".format(
            owner2, len(gow_df[gow_df["outcome"] == "lose"]), len(gow_df)
        )
    )
    print("There have been {} ties".format(len(gow_df[gow_df["outcome"] == "tie"])))

    last_matchup = gow_df.iloc[-1]
    print(
        "\nMost recent game: {:.0f} Week {:.0f}".format(
            last_matchup.year, last_matchup.week
        )
    )
    print(
        "{} {:.2f} - {:.2f} {}".format(
            last_matchup.team_owner,
            last_matchup.team_score,
            last_matchup.opp_score,
            last_matchup.opp_owner,
        )
    )

    team1 = get_team(league, team_owner=owner1)
    team2 = get_team(league, team_owner=owner2)
    division_standings = get_division_standings(league)
    print("\nThis season:\n-----------------------")
    print(f"{owner1} has a record of {team1.wins}-{team1.losses}-{team1.ties}")
    print(
        "They have averaged {:.2f} points per game.".format(
            df[
                (df["team_owner"] == owner1)
                & (df["year"] == league.year)
                & (df["is_meaningful_game"])
            ].team_score.mean()
        )
    )
    print(
        "{} is currently {}/{} in the {} division.".format(
            team1.team_name,
            division_standings[team1.division_name].index(team1) + 1,
            len(division_standings[team1.division_name]),
            team1.division_name,
        )
    )
    print()
    print(f"{owner2} has a record of {team2.wins}-{team2.losses}-{team2.ties}")
    print(
        "They have averaged {:.2f} points per game.".format(
            df[
                (df["team_owner"] == owner2)
                & (df["year"] == league.year)
                & (df["is_meaningful_game"])
            ].team_score.mean()
        )
    )
    print(
        "{} is currently {}/{} in the {} division.".format(
            team2.team_name,
            division_standings[team2.division_name].index(team2) + 1,
            len(division_standings[team2.division_name]),
            team2.division_name,
        )
    )

    return gow_df


def weekly_stats_analysis(df: pd.DataFrame, year: int, week: int) -> None:
    """Generate any league- or franchise-records for a given week.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        year (int): Year
        week (int): Week
    """
    df = df[df["is_meaningful_game"]]

    league_positive_stats_to_check = [
        {"stat": "team_score", "units": "pts", "high_first": True, "n": 3},
        {"stat": "team_score_adj", "units": "pts", "high_first": True, "n": 3},
        {"stat": "score_dif", "units": "pts", "high_first": True, "n": 3},
        {"stat": "lineup_efficiency", "units": "pts", "high_first": True, "n": 5},
        {"stat": "best_trio", "units": "pts", "high_first": True, "n": 5},
        {"stat": "QB_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "RB_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "WR_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "TE_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "D_ST_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "K_pts", "units": "pts", "high_first": True, "n": 5},
        {"stat": "bench_points", "units": "pts", "high_first": True, "n": 5},
        {"stat": "streak", "units": "pts", "high_first": True, "n": 3},
        {"stat": "season_wins", "units": "wins", "high_first": True, "n": 3},
        {"stat": "team_projection_beat", "units": "pts", "high_first": True, "n": 5},
    ]

    league_negative_stats_to_check = [
        {"stat": "team_score", "units": "pts", "high_first": False, "n": 3},
        {"stat": "team_score_adj", "units": "pts", "high_first": False, "n": 3},
        {"stat": "score_dif", "units": "pts", "high_first": False, "n": 3},
        {"stat": "lineup_efficiency", "units": "pts", "high_first": False, "n": 5},
        {"stat": "best_trio", "units": "pts", "high_first": False, "n": 5},
        {"stat": "QB_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "RB_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "WR_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "TE_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "D_ST_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "K_pts", "units": "pts", "high_first": False, "n": 5},
        {"stat": "bench_points", "units": "pts", "high_first": False, "n": 5},
        {"stat": "streak", "units": "pts", "high_first": False, "n": 3},
        {"stat": "team_projection_beat", "units": "pts", "high_first": False, "n": 5},
    ]
    franchise_positive_stats_to_check = [
        {"stat": "team_score", "units": "pts", "high_first": True, "n": 3},
        {"stat": "team_score_adj", "units": "pts", "high_first": True, "n": 3},
        {"stat": "score_dif", "units": "pts", "high_first": True, "n": 3},
        {"stat": "lineup_efficiency", "units": "pts", "high_first": True, "n": 1},
        {"stat": "best_trio", "units": "pts", "high_first": True, "n": 1},
        {"stat": "QB_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "RB_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "WR_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "TE_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "D_ST_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "K_pts", "units": "pts", "high_first": True, "n": 1},
        {"stat": "bench_points", "units": "pts", "high_first": True, "n": 1},
        {"stat": "streak", "units": "pts", "high_first": True, "n": 3},
        {"stat": "season_wins", "units": "wins", "high_first": True, "n": 1},
        {"stat": "team_projection_beat", "units": "pts", "high_first": True, "n": 3},
    ]
    franchise_negative_stats_to_check = [
        {"stat": "team_score", "units": "pts", "high_first": False, "n": 3},
        {"stat": "team_score_adj", "units": "pts", "high_first": False, "n": 3},
        {"stat": "score_dif", "units": "pts", "high_first": False, "n": 3},
        {"stat": "lineup_efficiency", "units": "pts", "high_first": False, "n": 1},
        {"stat": "best_trio", "units": "pts", "high_first": False, "n": 1},
        {"stat": "QB_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "RB_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "WR_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "TE_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "RB_WR_TE_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "D_ST_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "K_pts", "units": "pts", "high_first": False, "n": 1},
        {"stat": "bench_points", "units": "pts", "high_first": False, "n": 1},
        {"stat": "streak", "units": "pts", "high_first": False, "n": 3},
        {"stat": "team_projection_beat", "units": "pts", "high_first": False, "n": 3},
    ]

    print("----------------------------------------------------------------")
    print(
        "|                        Week {:2.0f} Analysis                            |".format(
            week
        )
    )
    print("----------------------------------------------------------------")

    print("League-wide POSITIVE stats\n--------------------------")
    for stat in league_positive_stats_to_check:
        print_records(
            df,
            year=year,
            week=week,
            stat=stat["stat"],
            stat_units=stat["units"],
            high_first=stat["high_first"],
            n=stat["n"],
        )

    # Good franchise awards
    print("\n\nFranchise POSITIVE stats\n--------------------------")
    for stat in franchise_positive_stats_to_check:
        print_franchise_records(
            df,
            year=year,
            week=week,
            stat=stat["stat"],
            stat_units=stat["units"],
            high_first=stat["high_first"],
            n=stat["n"],
        )

    print("\n\nLeague-wide NEGATIVE stats\n--------------------------")
    for stat in league_negative_stats_to_check:
        print_records(
            df,
            year=year,
            week=week,
            stat=stat["stat"],
            stat_units=stat["units"],
            high_first=stat["high_first"],
            n=stat["n"],
        )

    # Bad franchise records
    print("\n\nFranchise NEGATIVE stats\n--------------------------")
    for stat in franchise_negative_stats_to_check:
        print_franchise_records(
            df,
            year=year,
            week=week,
            stat=stat["stat"],
            stat_units=stat["units"],
            high_first=stat["high_first"],
            n=stat["n"],
        )


def season_stats_analysis(
    league: League, df: pd.DataFrame
) -> Dict[str, Dict[str, Union[str, int, float]]]:
    """Display season-bests and -worsts.

    Args:
        league (League): League object
        df (pd.DataFrame): Historical records dataframe

    Returns:
        Dict[str, Dict[str, Union[str, int, float]]]: Dictionary containing the season stats
    """
    # Filter the dataframe to only include meaningful games in the current year
    df = df[df["is_meaningful_game"]]
    df_current_year = df[df["year"] == league.year]

    # Calculate good awards
    season_stats_dict: Dict[str, Dict[str, Union[str, int, float]]] = {}
    season_stats_dict["most_wins"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str([(team.owner, team.wins) for team in league.teams]),
                "wins",
                "{:d}",
            ],
        )
    )
    season_stats_dict["highest_single_game_score"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(df_current_year[["team_owner", "team_score"]].values),
                    high_first=True,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["longest_win_streak"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(df_current_year[["team_owner", "streak"]].values),
                    high_first=True,
                ),
                "games",
                "{:d}",
            ],
        )
    )

    season_stats_dict["highest_avg_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["team_score"]
                        .mean()
                        .to_dict()
                        .items()
                    )
                ),
                "pts/gm",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["highest_avg_pts_against"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["opp_score"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                ),
                "pts/gm",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["highest_single_game_score_dif"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(df_current_year[["team_owner", "score_dif"]].values),
                    high_first=True,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["highest_single_game_pts_surprise"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year[["team_owner", "team_projection_beat"]].values
                    ),
                    high_first=True,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["highest_avg_lineup_efficiency"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["lineup_efficiency"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "",
                "{:7.2%}",
            ],
        )
    )

    # Calculate bad awards
    season_stats_dict["most_losses"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str([(team.owner, team.losses) for team in league.teams]),
                "losses",
                "{:d}",
            ],
        )
    )
    season_stats_dict["lowest_single_game_score"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year[df_current_year["team_score"] > 0][
                            ["team_owner", "team_score"]
                        ].values
                    ),
                    high_first=False,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["lowest_avg_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["team_score"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/gm",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["longest_loss_streak"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(df_current_year[["team_owner", "streak"]].values),
                    high_first=False,
                ),
                "games",
                "{:d}",
            ],
        )
    )
    season_stats_dict["lowest_avg_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["team_score"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/gm",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["lowest_avg_pts_against"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["opp_score"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/gm",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["lowest_single_game_score_dif"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(df_current_year[["team_owner", "score_dif"]].values),
                    high_first=False,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["lowest_single_game_pts_surprise"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year[["team_owner", "team_projection_beat"]].values
                    ),
                    high_first=False,
                ),
                "pts",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["lowest_avg_lineup_efficiency"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["lineup_efficiency"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "",
                "{:7.2%}",
            ],
        )
    )

    # Calculte good position awards
    season_stats_dict["most_QB_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["QB_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_RB_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["RB_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_WR_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["WR_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_TE_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["TE_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_RB_WR_TE_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["RB_WR_TE_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_D_ST_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["D_ST_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_K_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["K_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["most_bench_points"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["bench_points"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=True,
                ),
                "pts/week",
                "{:7.2f}",
            ],
        )
    )

    # Calculate bad position awards
    season_stats_dict["least_QB_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["QB_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_RB_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["RB_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_WR_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["WR_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_TE_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["TE_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_RB_WR_TE_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["RB_WR_TE_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_D_ST_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["D_ST_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_K_pts"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["K_pts"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/player",
                "{:7.2f}",
            ],
        )
    )
    season_stats_dict["least_bench_points"] = dict(
        zip(
            ["val", "owners", "val_units", "val_format"],
            [
                *get_leader_str(
                    list(
                        df_current_year.groupby("team_owner")["bench_points"]
                        .mean()
                        .to_dict()
                        .items()
                    ),
                    high_first=False,
                ),
                "pts/week",
                "{:7.2f}",
            ],
        )
    )

    # Flip the sign of some of the negative stats
    season_stats_dict["longest_loss_streak"]["val"] *= -1
    season_stats_dict["lowest_single_game_score_dif"]["val"] *= -1
    season_stats_dict["lowest_single_game_pts_surprise"]["val"] *= -1

    # Print good team awards
    print("----------------------------------------------------------------")
    print(
        "|             Season {:2.0f} Analysis                          |".format(
            league.year
        )
    )
    print("----------------------------------------------------------------")
    print(
        "Most wins this season              - {:.0f} {} - {}".format(
            float(season_stats_dict["most_wins"]["val"]),
            season_stats_dict["most_wins"]["val_units"],
            season_stats_dict["most_wins"]["owners"],
        )
    )
    print(
        "Highest single game score          - {:.0f} {} - {}".format(
            float(season_stats_dict["highest_single_game_score"]["val"]),
            season_stats_dict["highest_single_game_score"]["val_units"],
            season_stats_dict["highest_single_game_score"]["owners"],
        )
    )
    print(
        "Longest win streak this season     - {:.0f} {} - {}".format(
            float(season_stats_dict["longest_win_streak"]["val"]),
            season_stats_dict["longest_win_streak"]["val_units"],
            season_stats_dict["longest_win_streak"]["owners"],
        )
    )
    print(
        "Most PPG this season               - {:.1f} {} - {}".format(
            float(season_stats_dict["highest_avg_pts"]["val"]),
            season_stats_dict["highest_avg_pts"]["val_units"],
            season_stats_dict["highest_avg_pts"]["owners"],
        )
    )
    print(
        "Most PAPG this season              - {:.1f} {} - {}".format(
            float(season_stats_dict["highest_avg_pts_against"]["val"]),
            season_stats_dict["highest_avg_pts_against"]["val_units"],
            season_stats_dict["highest_avg_pts_against"]["owners"],
        )
    )
    print(
        "Highest score diff                 - {:.1f} {} - {}".format(
            float(season_stats_dict["highest_single_game_score_dif"]["val"]),
            season_stats_dict["highest_single_game_score_dif"]["val_units"],
            season_stats_dict["highest_single_game_score_dif"]["owners"],
        )
    )
    print(
        "Highest lineup efficiency          - {:.1%} - {}".format(
            float(season_stats_dict["highest_avg_lineup_efficiency"]["val"]),
            season_stats_dict["highest_avg_lineup_efficiency"]["owners"],
        )
    )

    # Bad team awards
    print()
    print(
        "Most losses this season           - {:.0f} {} - {}".format(
            float(season_stats_dict["most_losses"]["val"]),
            season_stats_dict["most_losses"]["val_units"],
            season_stats_dict["most_losses"]["owners"],
        )
    )
    print(
        "Lowest single game score          - {:.0f} {} - {}".format(
            float(season_stats_dict["lowest_single_game_score"]["val"]),
            season_stats_dict["lowest_single_game_score"]["val_units"],
            season_stats_dict["lowest_single_game_score"]["owners"],
        )
    )
    print(
        "Longest loss streak this season   - {:.0f} {} - {}".format(
            float(season_stats_dict["longest_loss_streak"]["val"]),
            season_stats_dict["longest_loss_streak"]["val_units"],
            season_stats_dict["longest_loss_streak"]["owners"],
        )
    )
    print(
        "Lowest PPG this season            - {:.1f} {} - {}".format(
            float(season_stats_dict["lowest_avg_pts"]["val"]),
            season_stats_dict["lowest_avg_pts"]["val_units"],
            season_stats_dict["lowest_avg_pts"]["owners"],
        )
    )
    print(
        "Lowest PAPG this season           - {:.1f} {} - {}".format(
            float(season_stats_dict["lowest_avg_pts_against"]["val"]),
            season_stats_dict["lowest_avg_pts_against"]["val_units"],
            season_stats_dict["lowest_avg_pts_against"]["owners"],
        )
    )
    print(
        "Lowest score diff                 - {:.1f} {} - {}".format(
            float(season_stats_dict["lowest_single_game_score_dif"]["val"]),
            season_stats_dict["lowest_single_game_score_dif"]["val_units"],
            season_stats_dict["lowest_single_game_score_dif"]["owners"],
        )
    )
    print(
        "Lowest lineup efficiency          - {:.1%} - {}".format(
            float(season_stats_dict["lowest_avg_lineup_efficiency"]["val"]),
            season_stats_dict["lowest_avg_lineup_efficiency"]["owners"],
        )
    )

    # Print good position awards
    print()
    print(
        "Most QB pts this season           - {:.1f} {} - {}".format(
            float(season_stats_dict["most_QB_pts"]["val"]),
            season_stats_dict["most_QB_pts"]["val_units"],
            season_stats_dict["most_QB_pts"]["owners"],
        )
    )
    print(
        "Most RB pts this season           - {:.1f} {} - {}".format(
            float(season_stats_dict["most_RB_pts"]["val"]),
            season_stats_dict["most_RB_pts"]["val_units"],
            season_stats_dict["most_RB_pts"]["owners"],
        )
    )
    print(
        "Most WR pts this season           - {:.1f} {} - {}".format(
            float(season_stats_dict["most_WR_pts"]["val"]),
            season_stats_dict["most_WR_pts"]["val_units"],
            season_stats_dict["most_WR_pts"]["owners"],
        )
    )
    print(
        "Most TE pts this season           - {:.1f} {} - {}".format(
            float(season_stats_dict["most_TE_pts"]["val"]),
            season_stats_dict["most_TE_pts"]["val_units"],
            season_stats_dict["most_TE_pts"]["owners"],
        )
    )
    print(
        "Most RB/WR/TE pts this season     - {:.1f} {} - {}".format(
            float(season_stats_dict["most_RB_WR_TE_pts"]["val"]),
            season_stats_dict["most_RB_WR_TE_pts"]["val_units"],
            season_stats_dict["most_RB_WR_TE_pts"]["owners"],
        )
    )
    print(
        "Most D/ST pts this season         - {:.1f} {} - {}".format(
            float(season_stats_dict["most_D_ST_pts"]["val"]),
            season_stats_dict["most_D_ST_pts"]["val_units"],
            season_stats_dict["most_D_ST_pts"]["owners"],
        )
    )
    print(
        "Most K pts this season            - {:.1f} {} - {}".format(
            float(season_stats_dict["most_K_pts"]["val"]),
            season_stats_dict["most_K_pts"]["val_units"],
            season_stats_dict["most_K_pts"]["owners"],
        )
    )
    print(
        "Most bench pts this season        - {:.1f} {} - {}".format(
            float(season_stats_dict["most_bench_points"]["val"]),
            season_stats_dict["most_bench_points"]["val_units"],
            season_stats_dict["most_bench_points"]["owners"],
        )
    )

    print()
    print(
        "Fewest QB pts this season         - {:.1f} {} - {}".format(
            float(season_stats_dict["least_QB_pts"]["val"]),
            season_stats_dict["least_QB_pts"]["val_units"],
            season_stats_dict["least_QB_pts"]["owners"],
        )
    )
    print(
        "Fewest RB pts this season         - {:.1f} {} - {}".format(
            float(season_stats_dict["least_RB_pts"]["val"]),
            season_stats_dict["least_RB_pts"]["val_units"],
            season_stats_dict["least_RB_pts"]["owners"],
        )
    )
    print(
        "Fewest WR pts this season         - {:.1f} {} - {}".format(
            float(season_stats_dict["least_WR_pts"]["val"]),
            season_stats_dict["least_WR_pts"]["val_units"],
            season_stats_dict["least_WR_pts"]["owners"],
        )
    )
    print(
        "Fewest TE pts this season         - {:.1f} {} - {}".format(
            float(season_stats_dict["least_TE_pts"]["val"]),
            season_stats_dict["least_TE_pts"]["val_units"],
            season_stats_dict["least_TE_pts"]["owners"],
        )
    )
    print(
        "Fewest RB/WR/TE pts this season   - {:.1f} {} - {}".format(
            float(season_stats_dict["least_RB_WR_TE_pts"]["val"]),
            season_stats_dict["least_RB_WR_TE_pts"]["val_units"],
            season_stats_dict["least_RB_WR_TE_pts"]["owners"],
        )
    )
    print(
        "Fewest D/ST pts this season       - {:.1f} {} - {}".format(
            float(season_stats_dict["least_D_ST_pts"]["val"]),
            season_stats_dict["least_D_ST_pts"]["val_units"],
            season_stats_dict["least_D_ST_pts"]["owners"],
        )
    )
    print(
        "Fewest K pts this season          - {:.1f} {} - {}".format(
            float(season_stats_dict["least_K_pts"]["val"]),
            season_stats_dict["least_K_pts"]["val_units"],
            season_stats_dict["least_K_pts"]["owners"],
        )
    )
    print(
        "Fewest bench pts this season      - {:.1f} {} - {}".format(
            float(season_stats_dict["least_bench_points"]["val"]),
            season_stats_dict["least_bench_points"]["val_units"],
            season_stats_dict["least_bench_points"]["owners"],
        )
    )

    return season_stats_dict
