from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class UserProfile(models.Model):
    """Extended user profile for playoff pool users"""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.display_name or 'No display name'}"


class League(models.Model):
    """League configuration and settings"""

    name = models.CharField(max_length=200)
    league_year = models.IntegerField(help_text="NFL season year for this league")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_leagues"
    )
    created_at = models.DateTimeField(default=timezone.now)

    # League settings
    num_teams = models.IntegerField(default=12)
    positions_included = models.JSONField(
        default=list, help_text="List of positions to include (QB, RB, WR, TE, K, DST)"
    )
    roster_config = models.JSONField(
        default=dict,
        help_text="Roster configuration: {position: count, flex: {eligible_positions: [RB, WR, TE], count: 1}}",
    )
    scoring_settings = models.JSONField(
        default=dict, help_text="Scoring multipliers for different stats"
    )

    # Draft status
    is_draft_complete = models.BooleanField(default=False)
    draft_started_at = models.DateTimeField(null=True, blank=True)
    draft_completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} (Created by {self.created_by.username})"

    def get_positions_display(self):
        """Return positions as comma-separated string"""
        if isinstance(self.positions_included, list):
            return ", ".join(self.positions_included)
        return "None set"

    def get_total_roster_size(self):
        """Calculate total roster size from roster config"""
        if not isinstance(self.roster_config, dict):
            return 0

        total = 0
        for position, count in self.roster_config.items():
            if position == "flex":
                # Flex is a dict with count
                if isinstance(count, dict):
                    total += count.get("count", 0)
                else:
                    total += count if isinstance(count, int) else 0
            else:
                total += count if isinstance(count, int) else 0
        return total


class LeagueMembership(models.Model):
    """Users belonging to leagues with their team names"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="members")
    team_name = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        # Remove unique_together constraint to allow multiple teams per user
        pass

    def __str__(self):
        username = self.user.username if self.user else "Unclaimed"
        return f"{username} - {self.team_name} ({self.league.name})"


class DraftedTeam(models.Model):
    """Players drafted to each team in the league"""

    league = models.ForeignKey(
        League, on_delete=models.CASCADE, related_name="drafted_players"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    team_membership = models.ForeignKey('LeagueMembership', on_delete=models.CASCADE, null=True, blank=True)
    team_name = models.CharField(max_length=100)

    # Player information
    gsis_id = models.CharField(max_length=50)
    player_name = models.CharField(max_length=200)
    position = models.CharField(max_length=10)
    nfl_team = models.CharField(max_length=10, help_text="NFL team abbreviation")
    fantasy_points = models.FloatField(default=0.0)

    # Draft metadata
    drafted_at = models.DateTimeField(default=timezone.now)
    draft_order = models.IntegerField(help_text="Order in which player was drafted")

    class Meta:
        unique_together = ("league", "gsis_id")
        ordering = ["draft_order"]

    def __str__(self):
        return f"{self.player_name} ({self.position}) -> {self.team_name} in {self.league.name}"


# New model for draftable playoff players
class PlayoffDraftablePlayer(models.Model):
    """Draftable playoff player record for each season"""

    year = models.IntegerField()
    gsis_id = models.CharField(max_length=50)
    player_id = models.CharField(max_length=50)
    full_name = models.CharField(max_length=200)
    team = models.CharField(max_length=10)
    position = models.CharField(max_length=10)
    fantasy_points = models.FloatField(default=0.0)
    draft_value = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("year", "gsis_id")
        indexes = [
            models.Index(fields=["year", "position", "team"]),
        ]
        ordering = ["position", "-draft_value"]


class LeagueScoringSetting(models.Model):
    """Custom scoring settings for each league"""

    league = models.ForeignKey(
        League, on_delete=models.CASCADE, related_name="custom_scoring_settings"
    )
    stat_name = models.CharField(
        max_length=100, help_text="Name of the statistical category"
    )
    multiplier = models.FloatField(
        default=0.0, help_text="Point multiplier for this stat"
    )
    is_defensive_stat = models.BooleanField(
        default=False, help_text="Whether this is a defensive/DST stat"
    )
    category = models.CharField(
        max_length=50,
        blank=True,
        help_text="Category grouping (passing, rushing, etc.)",
    )
    display_name = models.CharField(
        max_length=100, blank=True, help_text="Human-readable name for display"
    )

    class Meta:
        unique_together = ("league", "stat_name")
        ordering = ["category", "stat_name"]
        indexes = [
            models.Index(fields=["league", "is_defensive_stat"]),
        ]

    def __str__(self):
        return f"{self.league.name} - {self.display_name or self.stat_name}: {self.multiplier}"
