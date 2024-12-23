import datetime
import pytz
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import RequestContext

import espn_api
from espn_api.football import League

from fantasy_stats.email_notifications.email import send_new_league_added_alert
from .models import LeagueInfo
from src.doritostats.analytic_utils import get_naughty_list_str, season_stats_analysis
from src.doritostats.django_utils import (
    django_luck_index,
    django_power_rankings,
    django_simulation,
    django_season_stats,
    django_standings,
    django_strength_of_schedule,
    django_weekly_stats,
    get_distinct_leagues_previous_year,
    get_leagues_current_year,
    get_leagues_previous_year,
    ordinal,
)
from src.doritostats.fetch_utils import fetch_league

MIN_WEEK_TO_DISPLAY = 4  # Only run simulations after Week 4 has completed
N_SIMULATIONS = 500  # Default number of simulations to run
MAX_SIMULATIONS = 999  # Maximum number of simulations to run


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


# Create your views here.
def index(
    request,
    league_not_found: bool = False,
    league_id_access_denied: bool = False,
    unknown_error: bool = False,
):
    leagues_current_year = get_leagues_current_year()
    leagues_previous_year = get_leagues_previous_year()
    distinct_old_leagues = get_distinct_leagues_previous_year(leagues_current_year)

    return HttpResponse(
        render(
            request,
            "fantasy_stats/index.html",
            {
                "leagues_current_year": leagues_current_year,
                "leagues_previous_year": leagues_previous_year,
                "distinct_old_leagues": distinct_old_leagues,
                "league_not_found": league_not_found,
                "league_id_access_denied": league_id_access_denied,
                "unknown_error": unknown_error,
            },
        )
    )


def league_input(request):
    league_id = request.POST.get("league_id", None)
    league_year = int(request.POST.get("league_year", None))
    swid = request.POST.get("swid", None)
    espn_s2 = request.POST.get("espn_s2", None)

    print("Checking for League {} ({}) in database...".format(league_id, league_year))
    league_info_objs = LeagueInfo.objects.filter(
        league_id=league_id, league_year=league_year
    )
    try:
        if league_info_objs:
            league_info = league_info_objs[0]
            league_obj = fetch_league(league_id, league_year, swid, espn_s2)
            print(
                "League {} ({}) already exists in the database.".format(
                    league_id, league_year
                )
            )

        else:
            print(
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
            print(
                "League {} ({}) fetched and saved to the databse.".format(
                    league_id, league_year
                )
            )

            # Send an email notification that a new league has been added
            send_new_league_added_alert(league_info)

    except espn_api.requests.espn_requests.ESPNInvalidLeague as e:
        print(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        leagues_current_year = get_leagues_current_year()
        leagues_previous_year = get_leagues_previous_year()
        distinct_old_leagues = get_distinct_leagues_previous_year(leagues_current_year)
        return HttpResponse(
            render(
                request,
                "fantasy_stats/index.html",
                context={
                    "leagues_current_year": leagues_current_year,
                    "leagues_previous_year": leagues_previous_year,
                    "distinct_old_leagues": distinct_old_leagues,
                    "league_id": league_id,
                    "league_not_found": True,
                },
            )
        )
    except espn_api.requests.espn_requests.ESPNAccessDenied as e:
        print(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        leagues_current_year = get_leagues_current_year()
        leagues_previous_year = get_leagues_previous_year()
        distinct_old_leagues = get_distinct_leagues_previous_year(leagues_current_year)
        return HttpResponse(
            render(
                request,
                "fantasy_stats/index.html",
                context={
                    "leagues_current_year": leagues_current_year,
                    "leagues_previous_year": leagues_previous_year,
                    "distinct_old_leagues": distinct_old_leagues,
                    "league_id": league_id,
                    "league_id_access_denied": True,
                },
            )
        )
    except espn_api.requests.espn_requests.ESPNUnknownError as e:
        print(
            "League {} ({}) NOT FOUND! ESPN returned an error: {}".format(
                league_id, league_year, e
            )
        )
        leagues_current_year = get_leagues_current_year()
        leagues_previous_year = get_leagues_previous_year()
        distinct_old_leagues = get_distinct_leagues_previous_year(leagues_current_year)
        return HttpResponse(
            render(
                request,
                "fantasy_stats/index.html",
                context={
                    "leagues_current_year": leagues_current_year,
                    "leagues_previous_year": leagues_previous_year,
                    "distinct_old_leagues": distinct_old_leagues,
                    "league_id": league_id,
                    "unknown_error": True,
                },
            )
        )

    if league_obj.currentMatchupPeriod <= league_obj.firstScoringPeriod:
        # If the league hasn't started yet, display the "too soon" page
        return HttpResponse(
            render(
                request,
                "fantasy_stats/uh_oh_too_soon.html",
                context={
                    "league_id": league_id,
                    "league_year": league_year,
                    "page": "league_homepage",
                },
            )
        )
    else:
        return redirect(
            "/fantasy_stats/league/{}/{}".format(league_year, league_id, week=None)
        )


def copy_old_league(request, league_id: int):
    """This function takes the league_id of a league that exists for a previous year, and copies it to the current year.
    It does so by fetching the league credentials from the database, and then calling the league_input function.

    Args:
        request (HttpRequest): Django request
        league_id (int): ID of the league to copy

    Returns:
        HttpRequest: Rendered and redirected page
    """

    # Get the league info for the previous year
    previous_league = LeagueInfo.objects.filter(league_id=league_id).order_by(
        "-league_year"
    )[0]
    swid = previous_league.swid
    espn_s2 = previous_league.espn_s2

    # Add the old league to the current year
    current_year = (datetime.datetime.today() - datetime.timedelta(weeks=12)).year

    try:
        print(
            "Checking for League {} ({}) in database...".format(league_id, current_year)
        )
        league_info = LeagueInfo.objects.get(
            league_id=league_id, league_year=current_year
        )
        print("League found!")
        return league(request, league_id, current_year, week=None)

    except LeagueInfo.DoesNotExist:
        print(
            "League {} ({}) NOT FOUND! Fetching league from ESPN...".format(
                league_id, current_year
            )
        )
        league_obj = fetch_league(league_id, current_year, swid, espn_s2)
        league_info = LeagueInfo(
            league_id=league_id,
            league_year=current_year,
            swid=swid,
            espn_s2=espn_s2,
            league_name=league_obj.name,
        )
        league_info.save()
        print(
            "League {} ({}) fetched and saved to the databse.".format(
                league_id, current_year
            )
        )

        # Send an email notification that a new league has been added
        send_new_league_added_alert(league_info)

    if league_obj.currentMatchupPeriod <= league_obj.firstScoringPeriod:
        # If the league hasn't started yet, display the "too soon" page
        return HttpResponse(
            render(
                request,
                "fantasy_stats/uh_oh_too_soon.html",
                context={
                    "league_id": league_id,
                    "league_year": current_year,
                    "page": "league_homepage",
                },
            )
        )
    return redirect(
        "/fantasy_stats/league/{}/{}".format(current_year, league_id, week=None)
    )


def league(request, league_id: int, league_year: int, week: int = None):
    # Fetch the league
    league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    league_obj = fetch_league(
        league_info.league_id,
        league_info.league_year,
        league_info.swid,
        league_info.espn_s2,
    )

    # Set default week to display on page
    if week is None:
        week = get_default_week(league_obj)

    if week == 0 or not league_obj.draft:
        # If the league hasn't started yet, display the "too soon" page
        return HttpResponse(
            render(
                request,
                "fantasy_stats/uh_oh_too_soon.html",
                context={
                    "league_id": league_id,
                    "league_year": league_obj.year,
                    "page": "league_homepage",
                },
            )
        )

    else:
        box_scores = league_obj.box_scores(week)
        weekly_awards = django_weekly_stats(league_obj, week)
        power_rankings = django_power_rankings(league_obj, week)
        luck_index = django_luck_index(league_obj, week)
        strength_of_schedule, schedule_period = django_strength_of_schedule(
            league_obj, week
        )
        standings = django_standings(league_obj, week)
        naughty_list_str = get_naughty_list_str(league_obj, week)

        context = {
            "league_info": league_info,
            "league": league_obj,
            "page_week": week,
            "box_scores": box_scores,
            "weekly_awards": weekly_awards,
            "power_rankings": power_rankings,
            "luck_index": luck_index,
            "naughty_list_str": naughty_list_str,
            "strength_of_schedule": strength_of_schedule,
            "sos_weeks": schedule_period,
            "standings": standings,
            "scores_are_finalized": league_obj.current_week > week,
        }

        return HttpResponse(render(request, "fantasy_stats/league.html", context))


def standings(reqeust):
    return HttpResponse("League still exitst")


def all_leagues(request):
    league_objs = LeagueInfo.objects.order_by(
        "league_name", "-league_year", "league_id"
    )
    return render(request, "fantasy_stats/all_leagues.html", {"leagues": league_objs})


def simulation(
    request,
    league_id: int,
    league_year: int,
    week: int = None,
    n_simulations: int = None,
):
    # Set default number of simulations
    if n_simulations is None:
        n_simulations = N_SIMULATIONS

    # Limit the number of simulations to MAX_SIMULATIONS
    n_simulations = min(n_simulations, MAX_SIMULATIONS)

    # If the week is known, check if it is too early to display
    # If so, display the "too soon" page immediately
    if week is not None and week < MIN_WEEK_TO_DISPLAY:
        return HttpResponse(
            render(
                request,
                "fantasy_stats/uh_oh_too_soon.html",
                context={
                    "league_id": league_id,
                    "league_year": league_year,
                    "page": "playoff_simulations",
                },
            )
        )

    # Fetch the league
    league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    league_obj = fetch_league(
        league_info.league_id,
        league_info.league_year,
        league_info.swid,
        league_info.espn_s2,
    )

    # Set default week to display on page
    if week is None:
        week = get_default_week(league_obj)

    # If the week is less than the minimum week to display, display the "too soon" page
    if week < MIN_WEEK_TO_DISPLAY:
        return HttpResponse(
            render(
                request,
                "fantasy_stats/uh_oh_too_soon.html",
                context={
                    "league_id": league_id,
                    "league_year": league_year,
                    "page": "playoff_simulations",
                },
            )
        )

    else:
        playoff_odds, rank_dist, seeding_outcomes = django_simulation(
            league_obj, n_simulations
        )

    strength_of_schedule, schedule_period = django_strength_of_schedule(
        league_obj, week - 1
    )

    context = {
        "league_info": league_info,
        "league": league_obj,
        "page_week": week,
        "playoff_odds": playoff_odds,
        "rank_dist": rank_dist,
        "seeding_outcomes": seeding_outcomes,
        "strength_of_schedule": strength_of_schedule,
        "sos_weeks": schedule_period,
        "n_positions": len(league_obj.teams),
        "positions": [ordinal(i) for i in range(1, len(league_obj.teams) + 1)],
        "n_playoff_spots": league_obj.settings.playoff_team_count,
        "n_simulations": n_simulations,
        "simulation_presets": [100, 500, 999],
    }
    return HttpResponse(render(request, "fantasy_stats/simulation.html", context))


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


def index_gpt(request):
    return render(request, "fantasy_stats/index_gpt.html")


def handler404(request, *args, **argv):
    response = render("errors/404.html", {}, context_instance=RequestContext(request))
    response.status_code = 404
    return response
