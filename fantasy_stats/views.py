from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from .models import LeagueInfo
import datetime
from src.doritostats.fetch_utils import fetch_league
from src.doritostats.django_utils import (
    django_luck_index,
    django_power_rankings,
    django_standings,
    django_weekly_stats,
)


# Create your views here.
def index(request):
    current_year = (datetime.datetime.today() - datetime.timedelta(weeks=12)).year
    leagues_current_year = (
        LeagueInfo.objects.filter(league_year=current_year)
        .order_by("-league_id", "-league_year")
        .distinct("league_id", "league_year")
    )
    leagues_previous_year = (
        LeagueInfo.objects.filter(league_year__lt=current_year)
        .order_by("-league_id", "-league_year")
        .distinct("league_id", "league_year")
    )
    return HttpResponse(
        render(
            request,
            "fantasy_stats/index.html",
            {
                "leagues_current_year": leagues_current_year,
                "leagues_previous_year": leagues_previous_year,
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
        league = fetch_league(league_id, league_year, swid, espn_s2)
        league_info = LeagueInfo(
            league_id=league_id,
            league_year=league_year,
            swid=swid,
            espn_s2=espn_s2,
            league_name=league.name,
        )
        league_info.save()
        print(
            "League {} ({}) fetched and saved to the databse.".format(
                league_id, league_year
            )
        )

    return redirect(
        "/fantasy_stats/league/{}/{}".format(league_year, league_id, week=None)
    )


def league(request, league_id, league_year, week=None):
    league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    league = fetch_league(
        league_info.league_id,
        league_info.league_year,
        league_info.swid,
        league_info.espn_s2,
    )

    # Set default week to display on page
    if week is None:
        if datetime.datetime.now().strftime("%A") in ["Tuesday", "Wednesday"]:
            week = league.current_week - 1
        else:
            week = league.current_week

    if week == 0:
        box_scores, weekly_awards, power_rankings, luck_index, standings = (
            [],
            [],
            [],
            [],
            [],
        )

    else:
        box_scores = league.box_scores(week)
        weekly_awards = django_weekly_stats(league, week)
        power_rankings = django_power_rankings(league, week)
        luck_index = django_luck_index(league, week)
        standings = django_standings(league)

    context = {
        "league_info": league_info,
        "league": league,
        "page_week": week,
        "box_scores": box_scores,
        "weekly_awards": weekly_awards,
        "power_rankings": power_rankings,
        "luck_index": luck_index,
        "standings": standings,
    }
    return HttpResponse(render(request, "fantasy_stats/league.html", context))


def standings(reqeust):
    return HttpResponse("League still exitst")


def all_leagues(request):
    leagues = LeagueInfo.objects.order_by("-league_id", "-league_year")
    return render(request, "fantasy_stats/all_leagues.html", {"leagues": leagues})
