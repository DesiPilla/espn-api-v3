# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 20:38:57 2021

@author: desid
"""

from django.urls import path

from . import views

app_name = 'fantasy_stats'
urlpatterns = [
    # ex: /fantasy_stats/
    path('', views.index, name='index'),
    
    path('league_input', views.league_input, name='league_input'),

    # ex: /fantasy_stats/league/1086064
    path('league/<int:league_year>/<int:league_id>/', views.league, name='league'),

    # ex: fantasy_stats/all_leagues
    path('all_leagues/', views.all_leagues, name='all_leagues'),



    # # ex: /fantasy_stats/5/
    # path('<int:question_id>/', views.detail, name='detail'),
    
    # # ex: /fantasy_stats/5/results
    # path('<int:question_id>/results', views.results, name='results'),
    
    # # ex: /fantasy_stats/5/vote
    # path('<int:question_id>/vote/', views.vote, name='vote')
]