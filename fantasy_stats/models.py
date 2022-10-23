from django.db import models
from django.utils import timezone

import os, sys
sys.path.insert(0, os.path.join('..', 'code'))

import datetime 
# from espn_api import League
from .util_functions import *


# Create your models here.
class LeagueInfo(models.Model):
    league_id = models.IntegerField()
    league_year = models.IntegerField()
    swid = models.CharField(max_length=36)
    espn_s2 = models.CharField(max_length=500)
    league_name = models.CharField(max_length=50, default="<Name Missing>")

    # league_name = models.CharField(max_length=50, default="<Name Missing>")

    # league = fetch_league(league_id.value, league_year.value, swid.value, espn_s2.value)

    def __str__(self):
        return "{} ({})".format(self.league_id, self.league_year)


# heroku run bash
# python manage.py shell
# from fantasy_stats.models import LeagueInfo
# all_leagues = LeagueInfo.objects.all()
# for leg in all_leagues:
#     print(leg.league_id,'\n',leg.league_year,'\n',leg.swid,'\n',leg.espn_s2,'\n')