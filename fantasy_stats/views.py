from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import RequestContext
from .models import LeagueInfo
import datetime
from espn_api.football import League
from src.doritostats.django_utils import (
    django_luck_index,
    django_power_rankings,
    django_simulation,
    django_standings,
    django_strength_of_schedule,
    django_weekly_stats,
    ordinal,
)
from src.doritostats.fetch_utils import fetch_league
from src.doritostats.simulation_utils import simulate_season

MIN_WEEK_TO_DISPLAY = 4  # Only run simulations after Week 4 has completed
N_SIMULATIONS = 500


def get_default_week(league_obj: League):
    current_matchup_period = league_obj.settings.week_to_matchup_period[
        league_obj.current_week
    ]
    if datetime.datetime.now().strftime("%A") in ["Tuesday", "Wednesday"]:
        return max(current_matchup_period - 1, 1)
    else:
        return current_matchup_period


# Create your views here.
def index(request):
    now = datetime.datetime.now()
    current_year = now.year if now.month >= 5 else now.year - 1
    leagues_current_year = (
        LeagueInfo.objects.filter(league_year=current_year)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )
    leagues_previous_year = (
        LeagueInfo.objects.filter(league_year__lt=current_year)
        .order_by("league_name", "-league_year", "league_id")
        .distinct("league_name", "league_year", "league_id")
    )

    leagues_in_current_year = [
        league_obj.league_id for league_obj in leagues_current_year
    ]
    distinct_leagues = (
        LeagueInfo.objects.filter().order_by("-league_id").distinct("league_id")
    )
    distinct_old_leagues = [
        league_obj
        for league_obj in distinct_leagues
        if league_obj.league_id not in leagues_in_current_year
    ]
    return HttpResponse(
        render(
            request,
            "fantasy_stats/index.html",
            {
                "leagues_current_year": leagues_current_year,
                "leagues_previous_year": leagues_previous_year,
                "distinct_old_leagues": distinct_old_leagues,
            },
        )
    )


def league_input(request):
    league_id = request.POST.get("league_id", None)
    league_year = int(request.POST.get("league_year", None))
    swid = request.POST.get("swid", None)
    espn_s2 = request.POST.get("espn_s2", None)

    try:
        print(
            "Checking for League {} ({}) in database...".format(league_id, league_year)
        )
        league_info = LeagueInfo.objects.get(
            league_id=league_id, league_year=league_year
        )
        print("League found!")
    except LeagueInfo.DoesNotExist:
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

    if week == 0:
        (
            box_scores,
            weekly_awards,
            power_rankings,
            luck_index,
            strength_of_schedule,
            standings,
        ) = (
            [],
            [],
            [],
            [],
            [],
            [],
        )

    else:
        box_scores = league_obj.box_scores(week)
        weekly_awards = django_weekly_stats(league_obj, week)
        power_rankings = django_power_rankings(league_obj, week)
        luck_index = django_luck_index(league_obj, week)
        strength_of_schedule = django_strength_of_schedule(league_obj, week)
        standings = django_standings(league_obj)

    context = {
        "league_info": league_info,
        "league": league_obj,
        "page_week": week,
        "box_scores": box_scores,
        "weekly_awards": weekly_awards,
        "power_rankings": power_rankings,
        "luck_index": luck_index,
        "strength_of_schedule": strength_of_schedule,
        "standings": standings,
    }
    if league_obj.currentMatchupPeriod <= league_obj.firstScoringPeriod:
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
    if n_simulations is None:
        n_simulations = N_SIMULATIONS

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

    context = {
        "league_info": league_info,
        "league": league_obj,
        "page_week": week,
        "playoff_odds": playoff_odds,
        "rank_dist": rank_dist,
        "seeding_outcomes": seeding_outcomes,
        "strength_of_schedule": django_strength_of_schedule(league_obj, week),
        "n_positions": len(league_obj.teams),
        "positions": [ordinal(i) for i in range(1, len(league_obj.teams) + 1)],
        "n_playoff_spots": league_obj.settings.playoff_team_count,
        "n_simulations": n_simulations,
        "simulation_presets": [100, 500, 1000],
    }
    return HttpResponse(render(request, "fantasy_stats/simulation.html", context))


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
