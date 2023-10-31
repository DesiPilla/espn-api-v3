import datetime
from django.contrib.sitemaps import Sitemap
from .models import LeagueInfo


class StaticViewSitemap(Sitemap):
    def items(self):
        return [
            "/",
            "/fantasy_stats/",
            "/all_leagues/",
            "/fantasy_stats/all_leagues/",
        ]

    def location(self, item):
        return item


class LeagueHomeSitemap(Sitemap):
    def items(self):
        return LeagueInfo.objects.all()


class LeagueSimulationsSitemap(Sitemap):
    def items(self):
        return LeagueInfo.objects.filter()

    def location(self, obj):
        return f"/fantasy_stats/simulation/{obj.league_year}/{obj.league_id}/"
