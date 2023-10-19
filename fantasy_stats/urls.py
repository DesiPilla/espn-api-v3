# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 20:38:57 2021

@author: desid
"""

from django.urls import path

from . import views

app_name = "fantasy_stats"
urlpatterns = [
    # ex: /fantasy_stats/
    path("", views.index, name="index"),
    # ex: fantasy_stats/league_input
    path("league_input/", views.league_input, name="league_input"),
    # ex: /fantasy_stats/league/1086064
    path(
        "league/<int:league_year>/<int:league_id>/",
        views.league,
        {"week": None},
        name="league",
    ),
    path(
        "league/<int:league_year>/<int:league_id>/week=<int:week>/",
        views.league,
        name="league",
    ),
    path(
        "copy_old_league/<int:league_id>",
        views.copy_old_league,
        name="copy_old_league",
    ),
    # path('league/<int:league_year>/<int:league_id>/', views.league, {'week':None}, name='league'),
    # ex: fantasy_stats/all_leagues
    path("all_leagues/", views.all_leagues, name="all_leagues"),
    path(
        "simulation/<int:league_year>/<int:league_id>/",
        views.simulation,
        {"week": None},
        name="simulation",
    ),
    #
    #
    #
    # URLS THAT DO NOT WORK YET ARE IN THE TESTING PHASE
    path("index_gpt/", views.index_gpt, name="index_gpt"),
    path("test/", views.test, name="test"),
    path(
        "simulation/<int:league_year>/<int:league_id>/week=<int:week>/",
        views.simulation,
        name="simulation",
    ),
    # path("error404/", views.error404, name="error404"),
    # # ex: /fantasy_stats/5/
    # path('<int:question_id>/', views.detail, name='detail'),
    # # ex: /fantasy_stats/5/results
    # path('<int:question_id>/results', views.results, name='results'),
    # # ex: /fantasy_stats/5/vote
    # path('<int:question_id>/vote/', views.vote, name='vote')
]
