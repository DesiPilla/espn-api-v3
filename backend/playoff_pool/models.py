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
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_leagues')
    created_at = models.DateTimeField(default=timezone.now)
    
    # League settings
    num_teams = models.IntegerField(default=12)
    positions_included = models.JSONField(
        default=list, 
        help_text="List of positions to include (QB, RB, WR, TE, K, DST)"
    )
    scoring_settings = models.JSONField(
        default=dict,
        help_text="Scoring multipliers for different stats"
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


class LeagueMembership(models.Model):
    """Users belonging to leagues with their team names"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='members')
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
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name='drafted_players')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team_name = models.CharField(max_length=100)
    
    # Player information
    player_id = models.CharField(max_length=50)
    player_name = models.CharField(max_length=200)
    position = models.CharField(max_length=10)
    team = models.CharField(max_length=10, help_text="NFL team abbreviation")
    fantasy_points = models.FloatField(default=0.0)
    
    # Draft metadata
    drafted_at = models.DateTimeField(default=timezone.now)
    draft_order = models.IntegerField(help_text="Order in which player was drafted")
    
    class Meta:
        unique_together = ('league', 'player_id')
        ordering = ['draft_order']
    
    def __str__(self):
        return f"{self.player_name} ({self.position}) -> {self.team_name} in {self.league.name}"
