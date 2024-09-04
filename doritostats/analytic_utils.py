
import numpy as np
import pandas as pd
from copy import copy
from typing import Callable, Dict, List, Optional, Tuple
from espn_api.football import League, Team, Player
from espn_api.football.box_score import BoxScore
from sklearn import preprocessing
from doritostats import filter_utils


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

    return sorted(eligible_players, key=lambda x: x.points, reverse=True)[:n]


# def get_best_lineup(league: League, lineup: List[Player]) -> float:
#     """Returns the score of the best possible lineup for team during the loaded week."""
#     # Save full roster
#     saved_roster = copy(lineup)
#
#     # Find Best Lineup
#     best_lineup = []
#     # Get best RB before best RB/WR/TE
#     for slot in sorted(league.roster_settings["starting_roster_slots"].keys(), key=len):
#         num_players = league.roster_settings["starting_roster_slots"][slot]
#         best_players = get_top_players(saved_roster, slot, num_players)
#         best_lineup.extend(best_players)
#
#         # Remove selected players from consideration for other slots
#         for player in best_players:
#             saved_roster.remove(player)
#
#     return np.sum([player.points for player in best_lineup])


def get_best_trio(league: League, lineup: List[Player]) -> float:
    """Returns the the sum of the top QB/RB/Reciever trio for a team during the loaded week."""
    qb = get_top_players(lineup, "QB", 1)[0].points
    rb = get_top_players(lineup, "RB", 1)[0].points
    wr = get_top_players(lineup, "WR", 1)[0].points
    te = get_top_players(lineup, "TE", 1)[0].points
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


def get_score_surprise(league: League, lineup: List[Player]) -> float:
    """
    Returns the difference ("surprise") between a team's projected starting score and its actual score.
    """
    projected_score = np.sum(
        [
            player.projected_points
            for player in lineup
            if player.slot_position not in ("BE", "IR")
        ]
    )
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


def get_weekly_luck_index(league: League, team: Team, week: int) -> float:
    """
    This function returns an index quantifying how 'lucky' a team was in a given week

    Luck index:
        70% probability of playing a team with a lower total
        20% your play compared to previous weeks
        10% opp's play compared to previous weeks
    """
    opp = team.schedule[week - 1]
    num_teams = len(league.teams)

    # Set weights
    w_sched = 7
    w_team = 2
    w_opp = 1

    # Luck Index based on where the team and its opponent finished compared to the rest of the league
    rank = get_weekly_finish(league, team, week)
    opp_rank = get_weekly_finish(league, opp, week)

    if rank < opp_rank:  # If the team won...
        # Odds of this team playing a team with a higher score than it
        luck_index = w_sched * (rank - 1) / (num_teams - 1)
    elif rank > opp_rank:  # If the team lost or tied...
        # Odds of this team playing a team with a lower score than it
        luck_index = -w_sched * (num_teams - rank) / (num_teams - 1)

    # If the team tied...
    elif rank < (num_teams / 2):
        # They are only half as unlucky, because tying is not as bad as losing
        luck_index = -w_sched / 2 * (num_teams - rank - 1) / (num_teams - 1)
    else:
        # They are only half as lucky, because tying is not as good as winning
        luck_index = w_sched / 2 * (rank - 1) / (num_teams - 1)

    # Update luck index based on how team played compared to normal
    team_score = team.scores[week - 1]
    team_avg = np.mean(team.scores[:week])
    team_std = np.std(team.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (team_score - team_avg) / team_std

        # Noramlize the z-score so that a performance 2 std dev's away from the mean has an effect of 20% on the luck index
        z_norm = z / 2 * w_team
        luck_index += z_norm

    # Update luck index based on how opponent played compared to normal
    opp_score = opp.scores[week - 1]
    opp_avg = np.mean(opp.scores[:week])
    opp_std = np.std(opp.scores[:week])
    if team_std != 0:
        # Get z-score of the team's performance
        z = (opp_score - opp_avg) / opp_std

        # Noramlize the z-score so that a performance 2 std dev's away from the mean has an effect of 10% on the luck index
        z_norm = z / 2 * w_opp
        luck_index -= z_norm

    return luck_index / np.sum([w_sched, w_team, w_opp])


def get_season_luck_indices(league: League, week: int) -> Dict[Team, float]:
    """This function returns an index quantifying how 'lucky' a team was all season long (up to a certain week)"""
    luck_indices = {team: 0.0 for team in league.teams}
    for wk in range(1, week + 1):
        # Update luck_index for each team
        for team in league.teams:
            luck_indices[team] += get_weekly_luck_index(league, team, wk)

    return luck_indices


def calculate_win_pct(outcomes: np.array) -> float:
    """This function returns the win percentage of a team (excluding ties).

    Args:
        outcomes (np.array): Array of outcomes ('W', 'L', 'T')

    Returns:
        float: Win percentage
    """
    return sum(outcomes == "W") / sum((outcomes == "W") | (outcomes == "L"))


def get_remaining_schedule_difficulty(
    team: Team,
    week: int,
    strength: str = "points_for",
    league: Optional[League] = None,
) -> float:
    """
    This function returns the average score of a team's remaining opponents.

    The `strength` parameter defines how an opponent's "strength" is defined.
        - "points_for" means that difficulty is defined by the average points for scored by each of their remaining opponents.
        - "win_pct" means that the difficult is defined by the average winning percentage of each of their remaining opponents.
        - "power_rank" means that the difficult is defined by the average power rank of each of their remaining opponents.

    """
    remaining_schedule = team.schedule[week - 1 :]
    n_completed_weeks = len([o for o in team.outcomes if o != "U"])

    if strength == "points_for":
        # Get all scores from remaining opponenets through specified week
        remaining_strength = np.array(
            [opp.scores[: week - 1][:n_completed_weeks] for opp in remaining_schedule]
        ).flatten()

        # Exclude weeks that haven't occurred yet (not always applicable)
        remaining_strength = remaining_strength[:n_completed_weeks]

        # Return average score
        return remaining_strength.mean()

    elif strength == "win_pct":
        # Get win pct of remaining opponenets through specified week
        remaining_strength = np.array(
            [opp.outcomes[: week - 1] for opp in remaining_schedule]
        ).flatten()

        # Divide # of wins by (# of wins + # of losses) -- this excludes matches that tied or have not occurred yet
        return calculate_win_pct(remaining_strength)

    elif strength == "power_rank":
        power_rankings = {t: float(r) for r, t in league.power_rankings(week=week)}

        # Get all scores from remaining opponenets through specified week
        remaining_strength = np.array(
            [power_rankings[opp] for opp in remaining_schedule]
        ).flatten()

        # Return average power rank
        return remaining_strength.mean()

    else:
        raise Exception("Unrecognized parameter passed for `strength`")


def get_remaining_schedule_difficulty_df(league: League, week: int) -> pd.DataFrame:
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
        pd.DataFrame
    """
    remaining_difficulty_dict = {}  # type: ignore

    # Get the remaining SOS for each team
    for team in league.teams:
        remaining_difficulty_dict[team] = {}

        # SOS by points for
        remaining_difficulty_dict[team][
            "opp_points_for"
        ] = get_remaining_schedule_difficulty(team, week, strength="points_for")

        # SOS by win pct
        remaining_difficulty_dict[team][
            "opp_win_pct"
        ] = get_remaining_schedule_difficulty(team, week, strength="win_pct")

        # SOS by win pct
        remaining_difficulty_dict[team][
            "opp_power_rank"
        ] = get_remaining_schedule_difficulty(
            team, week, strength="power_rank", league=league
        )

    # Identify the min and max values for each SOS metric
    team_avg_score = [t.points_for / (week - 1) for t in league.teams]
    team_win_pct = [calculate_win_pct(np.array(t.outcomes)) for t in league.teams]
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

    return remaining_difficulty[
        ["opp_points_for", "opp_win_pct", "opp_power_rank", "overall_difficulty"]
    ].sort_values(by="overall_difficulty", ascending=False)


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


def get_leader_str(stats_list: list, high_first: bool = True) -> Tuple[float, str]:
    """Return a list of team owners who have the best stat,
    given a list of teams and stat values.

    Args:
        stats_list (list): list of teams and a stat value
          - Ex: [('Team 1', 103.7), ('Team 2', 83.7), ('Team 3', 98.8)]
        high_first (bool, optional): Are higher values better than lower values?. Defaults to True.

    Returns:
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
        return sorted_stats_list[0][1], "{}".format(", ".join(leaders))


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
    current_teams = df.query(f"year == {df.year.max()}").team_owner.unique()
    list_of_teams = df.groupby(["team_owner"]).nunique()
    list_of_teams = list_of_teams[
        (list_of_teams.year > 1) & list_of_teams.index.isin(current_teams)
    ].index.tolist()

    for team_owner in list_of_teams:
        # Get all rows for the given team
        team_df = df.query(f"team_owner == '{team_owner}'")

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
    df = df.query("outcome == 'win' & is_meaningful_game == True")
    leaderboard_df = (
        df.groupby("team_owner")
        .count()["outcome"]
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
    df = df.query("outcome == 'lose' & is_meaningful_game == True")
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
    gow_df = df.query(
        f"team_owner == '{owner1}' & opp_owner == '{owner2}' & is_meaningful_game == True"
    )
    gow_df.sort_values(["year", "week"], ascending=True, inplace=True)

    print(
        "{} has won {} / {} matchups.".format(
            owner1, len(gow_df.query("outcome == 'win'")), len(gow_df)
        )
    )
    print(
        "{} has won {} / {} matchups.".format(
            owner2, len(gow_df.query("outcome == 'lose'")), len(gow_df)
        )
    )
    print("There have been {} ties".format(len(gow_df.query("outcome == 'tie'"))))

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
            df.query(
                f"team_owner == '{owner1}' & year == {league.year} & is_meaningful_game == True"
            ).team_score.mean()
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
            df.query(
                f"team_owner == '{owner2}' & year == {league.year} & is_meaningful_game == True"
            ).team_score.mean()
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


def weekly_stats_analysis(df: pd.DataFrame, year: int, week: int) -> None:
    """Generate any league- or franchise-records for a given week.

    Args:
        df (pd.DataFrame): Historical stats dataframe
        year (int): Year
        week (int): Week
    """

    df = df.query("is_meaningful_game == True")

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
        "|                        Week {:2.0f} Analysis                      |".format(
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
    league: League, df: pd.DataFrame, week: Optional[int] = None
) -> None:
    """Display season-bests and -worsts.

    Args:
        league (League): League object
        df (pd.DataFrame): Historical records dataframe
        week (int, optional): Maximum week to include. Defaults to None.
    """
    if week is None:
        week = df.query(f"year == {df.year.max()}").week.max()

    current_matchup_period = league.settings.week_to_matchup_period[league.current_week]
    df = df.query("is_meaningful_game == True")
    df_current_year = df.query(f"year == {league.year}")
    df_current_week = df_current_year.query(f"week == {current_matchup_period - 1}")

    print("----------------------------------------------------------------")
    print(
        "|             Season {:2.0f} Analysis (through Week {:2.0f})           |".format(
            league.year, week
        )
    )
    print("----------------------------------------------------------------")

    # Good awards
    print(
        "Most wins this season              - {:.0f} wins - {}".format(
            *get_leader_str([(team.owner, team.wins) for team in league.teams])
        )
    )
    print(
        "Highest single game score          - {:.0f} pts - {}".format(
            *get_leader_str(
                df_current_year[["team_owner", "team_score"]].values, high_first=True
            )
        )
    )
    print(
        "Highest average points this season - {:.0f} pts/gm - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["team_score"]
                .to_dict()
                .items()
            )
        )
    )
    print(
        "Longest active win streak          - {:.0f} gms - {}".format(
            *get_leader_str(
                df_current_week[["team_owner", "streak"]].values, high_first=True
            )
        )
    )
    print(
        "Longest win streak this season     - {:.0f} gms - {}".format(
            *get_leader_str(
                df_current_year[["team_owner", "streak"]].values, high_first=True
            )
        )
    )
    print(
        "Most PPG this season               - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["team_score"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most PAPG this season              - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["opp_score_adj"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Highest score diff                 - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["score_dif"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Highest lineup efficiency          - {:.1%} - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["lineup_efficiency"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )

    # Bad awards
    print()
    print(
        "Most losses this season           - {:.0f} losses - {}".format(
            *get_leader_str([(team.owner, team.losses) for team in league.teams])
        )
    )
    print(
        "Lowest single game score          - {:.0f} pts - {}".format(
            *get_leader_str(
                df_current_year[["team_owner", "team_score"]].values, high_first=False
            )
        )
    )
    print(
        "Lowest average points this season - {:.0f} pts/gm - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["team_score"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Longest active loss streak        - {:.0f} gms - {}".format(
            *get_leader_str(
                df_current_week[["team_owner", "streak"]].values, high_first=False
            )
        )
    )
    print(
        "Longest loss streak this season   - {:.0f} gms - {}".format(
            *get_leader_str(
                df_current_year[["team_owner", "streak"]].values, high_first=False
            )
        )
    )
    print(
        "Lowest PPG this season            - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["team_score"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Lowest PAPG this season           - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["opp_score_adj"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Lowest score diff                 - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["score_dif"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Lowest lineup efficiency          - {:.1%} - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["lineup_efficiency"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )

    print()
    print(
        "Most QB pts this season           - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["QB_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most RB pts this season           - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["RB_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most WR pts this season           - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["WR_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most TE pts this season           - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["TE_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most RB/WR/TE pts this season     - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["RB_WR_TE_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most D/ST pts this season         - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["D_ST_pts"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )
    print(
        "Most K pts this season            - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner").mean()["K_pts"].to_dict().items(),
                high_first=True,
            )
        )
    )
    print(
        "Most bench pts this season        - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["bench_points"]
                .to_dict()
                .items(),
                high_first=True,
            )
        )
    )

    print()
    print(
        "Fewest QB pts this season         - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["QB_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest RB pts this season         - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["RB_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest WR pts this season         - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["WR_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest TE pts this season         - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["TE_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest RB/WR/TE pts this season   - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["RB_WR_TE_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest D/ST pts this season       - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["D_ST_pts"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest K pts this season          - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner").mean()["K_pts"].to_dict().items(),
                high_first=False,
            )
        )
    )
    print(
        "Fewest bench pts this season      - {:.1f} pts - {}".format(
            *get_leader_str(
                df_current_year.groupby("team_owner")
                .mean()["bench_points"]
                .to_dict()
                .items(),
                high_first=False,
            )
        )
    )
