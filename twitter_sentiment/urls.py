# -*- coding: utf-8 -*-
"""
Created on Wed Sep  8 20:38:57 2021

@author: desid
"""

from django.urls import path

from . import views

app_name = 'twitter_sentiment'
urlpatterns = [
    # ex: /twitter_sentiment/
    path('', views.index, name='index'),

    # ex: /twitter_sentiment/query_input
    path('query_input', views.query_input, name='query_input'),

    # ex: /twitter_sentiment/query=love
    path('query=<str:q>/', views.query, name='query'),

]