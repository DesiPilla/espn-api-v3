from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404

from .models import Question, League

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
    # league_id = int(request.POST.get('league_id'))
    # return redirect('fantasy_stats:home', league_id=league_id)

    league_id = request.POST.get('league_id', None)
    league_year = int(request.POST.get('league_year', None))
    swid = request.POST.get('swid', None)
    espn_s2 = request.POST.get('espn_s2', None)
    league = fetch_league(league_id, league_year, swid, espn_s2)

    request.session['league'] = league
    return redirect('fantasy_stats:home')



def home(request):
    league_id = request.POST.get('league_id', None)
    league_year = int(request.POST.get('league_year', None))
    swid = request.POST.get('swid', None)
    espn_s2 = request.POST.get('espn_s2', None)

    league = fetch_league(league_id, league_year, swid, espn_s2)
    # league = request.POST.get('league', None)
    return HttpResponse(render(request, 'fantasy_stats/index.html', {'league':league}))



def standings(reqeust):
    return HttpResponse('League still exitst')













def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'fantasy_stats/detail.html', {'question': question})

def results(request, question_id):
    return HttpResponse("You're looking at the results of question {}.".format(question_id))

def vote(request, question_id):
    return HttpResponse("You're voting on question {}.".format(question_id))
