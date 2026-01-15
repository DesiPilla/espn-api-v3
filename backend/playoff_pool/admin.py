from django.contrib import admin
from .models import (
    League,
    LeagueMembership,
    DraftedTeam,
    UserProfile,
    LeagueScoringSetting,
    CachedPlayerStats,
)
import logging

logger = logging.getLogger(__name__)


@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "num_teams",
        "created_by",
        "created_at",
        "is_draft_complete",
    )
    list_filter = ("is_draft_complete", "created_at")
    search_fields = ("name", "created_by__username")


@admin.register(LeagueMembership)
class LeagueMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "league", "is_admin", "team_name")
    list_filter = ("is_admin", "league")
    search_fields = ("user__username", "league__name", "team_name")


@admin.register(DraftedTeam)
class DraftedTeamAdmin(admin.ModelAdmin):
    list_display = ("team_name", "league", "user", "player_name", "position")
    list_filter = ("position", "league")
    search_fields = ("team_name", "player_name", "user__username")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name")
    search_fields = ("user__username", "display_name")


@admin.register(LeagueScoringSetting)
class LeagueScoringSettingAdmin(admin.ModelAdmin):
    list_display = (
        "league",
        "stat_name",
        "display_name",
        "multiplier",
        "is_defensive_stat",
        "category",
    )
    list_filter = ("league", "is_defensive_stat", "category")
    search_fields = ("league__name", "stat_name", "display_name")
    ordering = ("league", "category", "stat_name")

    def save_model(self, request, obj, form, change):
        """Override save to invalidate cache when scoring settings change"""
        super().save_model(request, obj, form, change)

        # Invalidate cache for this league
        deleted_count = CachedPlayerStats.objects.filter(league=obj.league).delete()[0]

        if deleted_count > 0:
            logger.info(
                f"Admin {request.user.username} updated scoring setting "
                f"'{obj.stat_name}' for league {obj.league.name}. "
                f"Cleared {deleted_count} cached entries."
            )
            self.message_user(
                request,
                f"Scoring setting updated. Cleared {deleted_count} cached entries for league '{obj.league.name}'. "
                f"Cache will be rebuilt on next request.",
            )

    def delete_model(self, request, obj):
        """Override delete to invalidate cache when scoring settings are deleted"""
        league = obj.league
        super().delete_model(request, obj)

        # Invalidate cache for this league
        deleted_count = CachedPlayerStats.objects.filter(league=league).delete()[0]

        if deleted_count > 0:
            logger.info(
                f"Admin {request.user.username} deleted scoring setting "
                f"'{obj.stat_name}' for league {league.name}. "
                f"Cleared {deleted_count} cached entries."
            )
            self.message_user(
                request,
                f"Scoring setting deleted. Cleared {deleted_count} cached entries for league '{league.name}'. "
                f"Cache will be rebuilt on next request.",
            )
