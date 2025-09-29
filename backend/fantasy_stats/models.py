from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        # soft delete instead of hard delete
        return super().update(deleted=True)

    def hard_delete(self):
        # if you need a true delete
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        # by default, filter out deleted=True
        return super().get_queryset().filter(deleted=False)

    def all_with_deleted(self):
        # optional: get everything, including deleted
        return super().get_queryset()


# Create your models here.
class LeagueInfo(models.Model):
    league_id = models.IntegerField()
    league_year = models.IntegerField()
    swid = models.CharField(max_length=100)
    espn_s2 = models.CharField(max_length=500)
    league_name = models.CharField(max_length=50, default="<Name Missing>")
    created_date = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)

    objects = SoftDeleteManager()  # default manager (excludes deleted)
    all_objects = models.Manager()  # backup manager (includes deleted)

    class Meta:
        # if you query this model without specifying manager, deleted=False is implied
        default_manager_name = "objects"

    def __str__(self):
        return "{} ({})".format(self.league_id, self.league_year)

    def get_absolute_url(self):
        return f"/fantasy_stats/league/{self.league_year}/{self.league_id}/"
