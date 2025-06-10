from django.db import models


# Create your models here.
class LeagueInfo(models.Model):
    league_id = models.IntegerField()
    league_year = models.IntegerField()
    swid = models.CharField(max_length=36)
    espn_s2 = models.CharField(max_length=500)
    league_name = models.CharField(max_length=50, default="<Name Missing>")
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} ({})".format(self.league_id, self.league_year)

    def get_absolute_url(self):
        return f"/fantasy_stats/league/{self.league_year}/{self.league_id}/"
