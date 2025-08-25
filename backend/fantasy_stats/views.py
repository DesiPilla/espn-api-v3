import datetime
import json
import logging
from typing import Optional
from django.core.cache import cache

import pytz
from django.http import HttpResponse, JsonResponse
from django.db.models import OuterRef, Subquery
from django.shortcuts import render, redirect, get_object_or_404
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.urls import path

import espn_api
from espn_api.football import League
from espn_api.requests.espn_requests import (
    ESPNInvalidLeague,
    ESPNAccessDenied,
    ESPNUnknownError,
)

from fantasy_stats.email_notifications.email import send_new_league_added_alert
from .models import LeagueInfo
from src.doritostats.analytic_utils import (
    get_naughty_list_str,
    get_naughty_players,
    get_lineup,
)
from src.doritostats.django_utils import (
    CURRENT_YEAR,
    django_luck_index,
    django_power_rankings,
    django_simulation,
    django_season_stats,
    django_standings,
    django_strength_of_schedule,
    django_weekly_stats,
    get_leagues_current_year,
    get_leagues_previous_year,
    ordinal,
)
from src.doritostats.exceptions import InactiveLeagueError
from src.doritostats.fetch_utils import fetch_league

logger = logging.getLogger(__name__)


MIN_WEEK_TO_DISPLAY = 4  # Only run simulations after Week 4 has completed
N_SIMULATIONS = 500  # Default number of simulations to run
MAX_SIMULATIONS = 500  # Maximum number of simulations to run
CACHE_DURATION = 10 * 60


def get_default_week(league_obj: League):
    current_matchup_period = league_obj.settings.week_to_matchup_period[
        league_obj.current_week
    ]

    if datetime.datetime.now(pytz.timezone("US/Eastern")).strftime("%A") in [
        "Tuesday",
        "Wednesday",
    ]:
        return current_matchup_period - 1
    else:
        return current_matchup_period


from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({"detail": "CSRF cookie set"})


@ensure_csrf_cookie
def react_app_view(request):
    return render(request, "index.html")


@require_POST
def league_input(request):

    data = json.loads(request.body)

    league_year = int(data.get("league_year"))
    league_id = int(data.get("league_id"))
    swid = data.get("swid", None)
    espn_s2 = data.get("espn_s2", None)

    logger.info(
        "Checking for League {} ({}) in database...".format(league_id, league_year)
    )
    league_info_objs = LeagueInfo.objects.filter(
        league_id=league_id, league_year=league_year
    )
    try:
        if league_info_objs:
            league_info = league_info_objs[0]
            league_obj = fetch_league(league_id, league_year, swid, espn_s2)
            logger.info(
                "League {} ({}) already exists in the database.".format(
                    league_id, league_year
                )
            )

        else:
            logger.info(
                "League {} ({}) NOT FOUND! Fetching league from ESPN...".format(
                    league_id, league_year
                )
            )
            league_obj = fetch_league(league_id, league_year, swid, espn_s2)
            league_info = LeagueInfo(
                league_id=league_id,
                league_year=league_year,
                swid=swid,
                espn_s2=espn_s2,
                league_name=league_obj.name,
            )
            league_info.save()
            logger.info(
                "League {} ({}) fetched and saved to the databse.".format(
                    league_id, league_year
                )
            )

            # Send an email notification that a new league has been added
            send_new_league_added_alert(league_info)

    except ESPNInvalidLeague as e:
        logger.info(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        return JsonResponse(
            {
                "error": f"League ID {league_id} not found. Please check that you have entered the correct league ID."
            },
            status=400,
        )
    except ESPNAccessDenied as e:
        logger.info(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        return JsonResponse(
            {"error": f"SWID or espn_s2 is incorrect. Please try again."},
            status=400,
        )
    except InactiveLeagueError as e:
        logger.info(
            "League {} ({}) IS NOT ACTIVE YET! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        return JsonResponse(
            {
                "error": f"League ID {league_id} not found. Please check that you have entered the correct league ID."
            },
            status=400,
        )
    except ESPNUnknownError as e:
        logger.info(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        return JsonResponse(
            {
                "error": f"An unknown error has occurred. Please check that you have entered the correct league ID, SWID, and espn_s2. "
            },
            status=400,
        )

    if league_obj.currentMatchupPeriod <= league_obj.firstScoringPeriod:
        # If the league hasn't started yet, display the "too soon" page
        return redirect(f"/too-early/league_homepage")

    else:
        return JsonResponse(
            {
                "success": True,
                "redirect_url": f"/fantasy_stats/league/{league_year}/{league_id}/",
            }
        )


def season_stats(
    request,
    league_id: int,
    league_year: int,
):
    # Fetch the league
    league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    league_obj = fetch_league(
        league_info.league_id,
        league_info.league_year,
        league_info.swid,
        league_info.espn_s2,
    )

    (
        best_team_stats_list,
        worst_team_stats_list,
        best_position_stats_list,
        worst_position_stats_list,
    ) = django_season_stats(league=league_obj)

    context = {
        "league_info": league_info,
        "scores_are_finalized": league_obj.is_season_complete,
        "best_team_stats": best_team_stats_list,
        "worst_team_stats": worst_team_stats_list,
        "best_position_stats": best_position_stats_list,
        "worst_position_stats": worst_position_stats_list,
    }
    return HttpResponse(render(request, "fantasy_stats/season_stats.html", context))


#############################################################
## VIEWS THAT DO NOT WORK YET AND ARE IN THE TESTING PHASE ##
#############################################################


def test(request):
    return render(request, "fantasy_stats/test.html")


@api_view(["GET"])
def test_react(request):
    return render(request, "fantasy_stats/test-react.html")


def index_gpt(request):
    return render(request, "fantasy_stats/index_gpt.html")


def handler404(request, *args, **argv):
    response = render("errors/404.html", {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response


from django.views.generic import View


class ReactAppView(View):
    template_name = "index.html"


def leagues_data(request):
    league_info_current_year = get_leagues_current_year()
    league_info_previous_year = get_leagues_previous_year()

    leagues_current_year = [
        {
            "league_id": league.league_id,
            "league_year": league.league_year,
            "league_name": league.league_name,
            "swid": league.swid,
            "espn_s2": league.espn_s2,
        }
        for league in league_info_current_year
    ]
    leagues_previous_year = [
        {
            "league_id": league.league_id,
            "league_year": league.league_year,
            "league_name": league.league_name,
            "swid": league.swid,
            "espn_s2": league.espn_s2,
        }
        for league in league_info_previous_year
    ]

    return JsonResponse(
        {
            "leagues_current_year": leagues_current_year,
            "leagues_previous_year": leagues_previous_year,
        },
        safe=False,
    )


def get_league_details(request, year, league_id):
    if request.method == "GET":
        # Fetch the league data (for example from the League model)
        league = get_object_or_404(LeagueInfo, league_year=year, league_id=league_id)

        # Prepare the data to be returned as JSON
        data = {
            "league_name": league.league_name,
            "league_year": league.league_year,
            "league_id": league.league_id,
        }
        return JsonResponse(data)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


def get_distinct_leagues_previous_year(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # For each row in LeagueInfo, create a subquery to fetch the latest league_year for the same league_id.
    # Make sure that the league_year is less than 2025
    latest_league_qs = LeagueInfo.objects.filter(
        league_id=OuterRef("league_id"),
        league_year__lt=CURRENT_YEAR,
    ).order_by("-league_year")

    # Then get the distinct leagues with the most recent year per league_id
    distinct_leagues = LeagueInfo.objects.filter(
        league_year=Subquery(latest_league_qs.values("league_year")[:1])
    ).order_by("league_name")

    # Get the leagues for the current year
    leagues_current_year = get_leagues_current_year()

    return JsonResponse(
        [
            {
                "league_year": league_obj.league_year,
                "league_id": league_obj.league_id,
                "league_name": league_obj.league_name,
                "league_swid": league_obj.swid,
                "league_espn_s2": league_obj.espn_s2,
            }
            for league_obj in distinct_leagues
            if league_obj.league_id not in leagues_current_year
            # if league_obj.league_id == 754151273  # DELETE ME
            # if league_obj.league_id == 1086064  # DELETE ME
        ],
        safe=False,
    )


@require_POST
def copy_old_league(request, league_id: int):
    print(f"LOGGER NAME: {logger.name}")

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Get the most recent league for this ID
    previous_leagues = LeagueInfo.objects.filter(league_id=league_id).order_by(
        "-league_year"
    )
    if not previous_leagues.exists():
        return JsonResponse(
            {"error": f"No previous league found with ID {league_id}"}, status=404
        )

    previous_league = previous_leagues[0]
    swid = previous_league.swid
    espn_s2 = previous_league.espn_s2

    current_year = (datetime.datetime.today() - datetime.timedelta(weeks=12)).year

    try:
        # Check if league already exists
        league_info = LeagueInfo.objects.get(
            league_id=league_id, league_year=current_year
        )
        return JsonResponse(
            {
                "success": True,
                "redirect_url": f"/fantasy_stats/league/{current_year}/{league_id}/",
            }
        )

    except LeagueInfo.DoesNotExist:
        try:
            league_obj = fetch_league(league_id, current_year, swid, espn_s2)
        except InactiveLeagueError as e:
            logger.info(
                "League {} ({}) IS NOT ACTIVE YET! ESPN returned an error: {}".format(
                    league_id, current_year, e
                )
            )
            return JsonResponse(
                {
                    "error": f"League ID {league_id} not found. Please check that you have entered the correct league ID."
                },
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": f"Failed to fetch league: {str(e)}"}, status=500)

    # Save new league info
    try:
        league_info = LeagueInfo(
            league_id=league_id,
            league_year=current_year,
            swid=swid,
            espn_s2=espn_s2,
            league_name=league_obj.name,
        )
        league_info.save()
        send_new_league_added_alert(league_info)
    except Exception as e:
        return JsonResponse({"error": f"Failed to save league: {str(e)}"}, status=500)

    # Handle early season case
    if league_obj.currentMatchupPeriod <= league_obj.firstScoringPeriod:
        return JsonResponse(
            {
                "error": "League season hasn't started yet. Please try again later.",
                "type": "too_soon",
            },
            status=400,
        )

    return JsonResponse(
        {
            "success": True,
            "redirect_url": f"/fantasy_stats/league/{current_year}/{league_id}/",
        }
    )


def get_cached_league(league_id: int, league_year: int) -> League:
    """
    Fetches the league object from the cache or creates a new one if it doesn't exist.
    """
    cache_key = f"league_obj_{league_id}_{league_year}"
    league_obj = cache.get(cache_key)

    if not league_obj:
        league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
        league_obj = fetch_league(league_id=league_id, year=league_year, swid=league_info.swid, espn_s2=league_info.espn_s2)
        cache.set(cache_key, league_obj, timeout=CACHE_DURATION)

    return league_obj

def preload_league(request, league_id: int, league_year: int):
    """
    Preloads the league data and caches it for faster access.
    """
    get_cached_league(league_id=league_id, league_year=league_year)
    return JsonResponse({"status": "ready"})


@require_GET
def get_league_endpoint(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:
    """
    Returns the endpoint for the given league.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    return JsonResponse({"endpoint": league.endpoint})


@require_GET
def get_current_week(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:
    """
    Returns the current week for the given league.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    return JsonResponse({"current_week": league.current_week})


@require_GET
def box_scores_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the box scores for the given week.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)

    # Load box scores for specified week
    box_scores = league.box_scores(week)

    # Get the scores for each team
    formatted_box_scores = []
    for matchup in box_scores:
        if not (matchup.home_team and matchup.away_team):
            # Skip byes
            continue

        formatted_box_scores.append(
            {
                "home_team": matchup.home_team.team_name,
                "home_score": matchup.home_score,
                "away_team": matchup.away_team.team_name,
                "away_score": matchup.away_score,
            }
        )
    return JsonResponse(formatted_box_scores, safe=False)


@require_GET
def weekly_awards_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the weekly awards for the given week.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    best_awards, worst_awards = django_weekly_stats(league, week)

    # Combine awards and stats into a response
    response_data = {
        "bestAwards": best_awards,
        "worstAwards": worst_awards,
    }

    return JsonResponse(response_data, safe=False)


@require_GET
def power_rankings_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the power rankings for the given week.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    power_rankings = django_power_rankings(league, week)

    return JsonResponse(power_rankings, safe=False)


@require_GET
def luck_index_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the luck index for the given week.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    luck_index = django_luck_index(league, week)

    return JsonResponse(luck_index, safe=False)


@require_GET
def naughty_list_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the naughty list for the given week.
    """
    """This function identifies all players that were started by their owners, but were inactive or on bye.

    Args:
        league (League): League object
        week (int): The week to check for inactive players

    Returns:
        List[str]: A list of strings that list all players that were started by their owners, but were inactive or on bye.
    """
    # Fetch the league
    league = get_cached_league(league_id=league_id, league_year=league_year)

    # Identify all players that were started by their owners, but were inactive or on bye
    naughty_list = []
    for team in league.teams:
        lineup = get_lineup(league, team, week)
        naughty_players = get_naughty_players(lineup, week)
        for player in naughty_players:
            naughty_list.append(
                {
                    "team": team.owner,
                    "player": player.name,
                    "active_status": player.active_status,
                }
            )

    return JsonResponse(naughty_list, safe=False)


@require_GET
def standings_view(
    request,
    league_id: int,
    league_year: int,
    week: int,
) -> JsonResponse:
    """
    Fetches the standings for the given week.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    standings = django_standings(league, week)

    return JsonResponse(standings, safe=False)


@require_GET
def check_league_status(request, league_year: int, league_id: int) -> JsonResponse:
    """
    Checks if the week is 0 or if the league draft has not occurred.
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)
    if league.current_week <= 1:
        return JsonResponse({"status": "too_soon", "message": "League has not started yet."}, status=400)
    if not league.draft:
        return JsonResponse({"status": "too_soon", "message": "League draft has not occurred."}, status=400)
    return JsonResponse({"status": "ok", "message": "League is ready."})


@require_GET
def league_settings(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:
    """
    Fetches the various settings for the league
    """
    league = get_cached_league(league_id=league_id, league_year=league_year)

    return JsonResponse(
        {
            "n_playoff_spots": league.settings.playoff_team_count,
            "n_teams": league.settings.team_count,
            "n_regular_season_weeks": league.settings.reg_season_count,
            "regular_season_complete": league.current_week
            > league.settings.reg_season_count,
            "playoffs_complete": league.current_week
            >= len(league.settings.matchup_periods),
            "season_complete": league.is_season_complete,
        }
    )


@require_GET
def simulate_playoff_odds_view(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:
    # Validate and process the parameters
    try:
        n_simulations = int(request.GET.get("n_simulations", N_SIMULATIONS))
        week = request.GET.get("week", None)
        if week is not None:
            week = int(week)
    except ValueError:
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    # Limit maximum number of simulations to protect server
    n_simulations = min(n_simulations, MAX_SIMULATIONS)

    # Fetch the league
    league = get_cached_league(league_id=league_id, league_year=league_year)

    # Set default week to display on page
    if week is None:
        week = get_default_week(league)

    # If the week is less than the minimum week to display, display the "too soon" page
    if week < MIN_WEEK_TO_DISPLAY:
        return JsonResponse(
            {
                "error": f"Playoff simulations are not available until after Week {MIN_WEEK_TO_DISPLAY}. Please try again later.",
                "type": "too_soon",
            },
            status=400,
        )

    # Generate a cache key based on league_id, league_year, week, and n_simulations
    cache_key = (
        f"playoff_odds_{league_id}_{league_year}_week_{week}_sim_{n_simulations}"
    )
    cached_result = cache.get(cache_key)

    if cached_result:
        return JsonResponse(cached_result, safe=False)

    # Perform the simulation if no cached result is found
    playoff_odds, rank_dist, seeding_outcomes = django_simulation(
        league=league, n_simulations=n_simulations, week=week
    )

    result = {
        "playoff_odds": playoff_odds,
        "rank_distribution": rank_dist,
        "seeding_outcomes": seeding_outcomes,
        "n_simulations": n_simulations,
    }

    # Cache the result for 1 hour
    cache.set(cache_key, result, timeout=CACHE_DURATION)

    return JsonResponse(result, safe=False)


@require_GET
def remaining_strength_of_schedule_view(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:
    # Validate and process the parameters
    try:
        week = request.GET.get("week", None)
        if week is not None:
            week = int(week)
    except ValueError:
        return JsonResponse({"error": "Invalid parameters."}, status=400)

    # Generate a cache key based on league_id, league_year, week
    cache_key = f"remaining_sos_{league_id}_{league_year}_week_{week}"
    cached_result = cache.get(cache_key)

    # Fetch the league
    league = get_cached_league(league_id=league_id, league_year=league_year)

    if cached_result:
        return JsonResponse(cached_result, safe=False)

    strength_of_schedule, schedule_period = django_strength_of_schedule(
        league=league, week=week
    )

    result = {
        "remaining_strength_of_schedule": strength_of_schedule,
        "min_week": schedule_period[0],
        "max_week": schedule_period[1],
    }

    # Cache the result
    cache.set(cache_key, result, timeout=CACHE_DURATION)

    return JsonResponse(result, safe=False)


@require_GET
def season_records(
    request,
    league_id: int,
    league_year: int,
) -> JsonResponse:

    # Generate a cache key based on league_id, league_year, week
    cache_key = f"season_records_{league_id}_{league_year}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return JsonResponse(cached_result, safe=False)

    # Fetch the league
    league = get_cached_league(league_id=league_id, league_year=league_year)

    # Get the season records
    (
        best_team_stats_list,
        worst_team_stats_list,
        best_position_stats_list,
        worst_position_stats_list,
    ) = django_season_stats(league=league)

    result = {
        "best_team_stats": best_team_stats_list,
        "worst_team_stats": worst_team_stats_list,
        "best_position_stats": best_position_stats_list,
        "worst_position_stats": worst_position_stats_list,
    }

    # Cache the result
    cache.set(cache_key, result, timeout=CACHE_DURATION)

    return JsonResponse(result, safe=True)
