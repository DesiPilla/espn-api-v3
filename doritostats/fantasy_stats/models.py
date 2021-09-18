from django.db import models
from django.utils import timezone

import os, sys
sys.path.insert(0, os.path.join('..', 'code'))

import datetime 
# from espn_api import League
from util_functions import *


# Create your models here.
class LeagueInfo(models.Model):
    league_id = models.IntegerField()
    league_year = models.IntegerField()
    swid = models.CharField(max_length=50)
    espn_s2 = models.CharField(max_length=300)
    league_name = models.CharField(max_length=50, default="<Name Missing>")

    # league_name = models.CharField(max_length=50, default="<Name Missing>")

    # league = fetch_league(league_id.value, league_year.value, swid.value, espn_s2.value)

    def __str__(self):
        return "{} ({})".format(self.league_id, self.league_year)


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    
    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        return self.pub_date >= timezone.timenow() - datetime.timedelta(days=1)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    
    def __str__(self):
        return self.choice_text
    

