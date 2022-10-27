import datetime
from django.db import models
from django.utils import timezone

import os
import sys
sys.path.insert(0, os.path.join('..', 'code'))

# from espn_api import League


# Create your models here.
class LeagueInfo(models.Model):
    league_id = models.IntegerField()
    league_year = models.IntegerField()
    swid = models.CharField(max_length=36)
    espn_s2 = models.CharField(max_length=500)
    league_name = models.CharField(max_length=50, default="<Name Missing>")

    def __str__(self):
        return "{} ({})".format(self.league_id, self.league_year)
