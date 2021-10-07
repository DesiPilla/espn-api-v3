from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404

from .models import Queston, LeagueInfo

import os, sys
sys.path.insert(0, os.path.join('..', 'code'))
os.environ['swid'] = '55B70875-0A4B-428F-B708-750A4BB28FA1'
os.environ['espn_s2'] = 'AEApIqrIV9DE%2F6ZyCAHsoG7FnThiXorn2ejnLGJol8qqRUDI6IVkY11AZLoYlNgj6uoA1M3aSYjcJ2%2F1NiBBzvyI4GzanP%2BCmvF0DhcYSDxaGFzBwYKhzXxkHGd2a9rAC%2Bz3A%2FT3EgEIg8%2FqiUEGDiUhtrRpwQBtDHzelXXBjyCbjH2kSNYBrhON5pZPcvNbJhwRZXr%2F%2Fd1tVQQ7U4FnltTB7VGFPcf7TwT4RYuylGyHixEQAdtzb4YAcbXJOJKNBJF0%2BJgLg2mAb4F4REaXbyX8'

from util_functions import *

# Create your views here.
def index(request):
    # Code
    most_recent_questions = Question.objects.order_by('-pub_date')[:5]
    # Map variables to context
    context = {'most_recent_questions': most_recent_questions}
    
    return HttpResponse(render(request, 'fantasy_stats/index.html', context))



def league_input(request):
    league_id = request.POST.get('league_id', None)
    league_year = int(request.POST.get('league_year', None))
    swid = request.POST.get('swid', None)
    espn_s2 = request.POST.get('espn_s2', None)

    try: 
        league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    except LeagueInfo.DoesNotExist:  
        league = fetch_league(league_id, league_year, swid, espn_s2)  
        league_info = LeagueInfo(league_id=league_id, 
                                league_year=league_year, 
                                swid=swid, 
                                espn_s2=espn_s2, 
                                league_name=league.name)
        league_info.save()

    return redirect('league/{}/{}'.format(league_year, league_id))

def league(request, league_id, league_year):
    league_info = LeagueInfo.objects.get(league_id=league_id, league_year=league_year)
    league = fetch_league(league_info.league_id, league_info.league_year, league_info.swid, league_info.espn_s2)
    
    weekly_awards = django_weekly_stats(league, league.current_week-1)
    power_rankings = django_power_rankings(league, league.current_week-1)
    luck_index = django_luck_index(league, league.current_week-1)
    standings = django_standings(league)

    context = {'league_info':league_info, 
               'league':league,
               'weekly_awards':weekly_awards,
               'power_rankings':power_rankings,
               'luck_index':luck_index,
               'standings':standings
               }
    return HttpResponse(render(request, 'fantasy_stats/league.html', context))


def standings(reqeust):
    return HttpResponse('League still exitst')


def all_leagues(request):
    leagues = LeagueInfo.objects.order_by('-league_id', '-league_year')
    return render(request, 'fantasy_stats/all_leagues.html', {'leagues':leagues})










def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'fantasy_stats/detail.html', {'question': question})

def results(request, question_id):
    return HttpResponse("You're looking at the results of question {}.".format(question_id))

def vote(request, question_id):
    return HttpResponse("You're voting on question {}.".format(question_id))
