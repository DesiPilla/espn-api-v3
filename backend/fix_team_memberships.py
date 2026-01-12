#!/usr/bin/env python
"""
Fix team_membership links for DraftedTeam records.
This script links all DraftedTeam records to their corresponding LeagueMembership
based on matching team_name and league.
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'doritostats.settings')
django.setup()

from playoff_pool.models import DraftedTeam, LeagueMembership, League
from django.core.cache import cache

def fix_team_memberships():
    """Link DraftedTeam records to LeagueMembership records by team_name"""
    
    # Get all leagues
    leagues = League.objects.all()
    
    for league in leagues:
        print(f"\nProcessing league: {league.name} (ID: {league.id})")
        
        # Get all memberships for this league
        memberships = LeagueMembership.objects.filter(league=league)
        
        for membership in memberships:
            # Find all DraftedTeam records with matching team_name
            drafted_teams = DraftedTeam.objects.filter(
                league=league,
                team_name=membership.team_name
            )
            
            count = drafted_teams.count()
            if count > 0:
                # Update all matching records
                drafted_teams.update(team_membership=membership)
                user_str = membership.user.username if membership.user else "Unclaimed"
                print(f"  - Updated {count} players for team '{membership.team_name}' (Owner: {user_str})")
        
        # Clear cache for this league
        cache_key = f"playoff_points_league_{league.id}_year_{league.league_year}"
        cache.delete(cache_key)
        print(f"  - Cleared cache for league")

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing team_membership links for DraftedTeam records")
    print("=" * 60)
    fix_team_memberships()
    print("\n" + "=" * 60)
    print("Done! Team memberships have been fixed.")
    print("=" * 60)
