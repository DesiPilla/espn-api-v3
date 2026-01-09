from django.contrib import admin
from .models import League, LeagueMembership, DraftedTeam, UserProfile


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
