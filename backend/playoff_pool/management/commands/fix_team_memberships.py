"""
Management command to fix team_membership links for DraftedTeam records
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from backend.playoff_pool.models import DraftedTeam, LeagueMembership, League


class Command(BaseCommand):
    help = "Fix team_membership links for DraftedTeam records based on team_name"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("Fixing team_membership links for DraftedTeam records")
        self.stdout.write("=" * 60)

        # Get all leagues
        leagues = League.objects.all()

        for league in leagues:
            self.stdout.write(f"\nProcessing league: {league.name} (ID: {league.id})")

            # Get all memberships for this league
            memberships = LeagueMembership.objects.filter(league=league)

            for membership in memberships:
                # Find all DraftedTeam records with matching team_name
                drafted_teams = DraftedTeam.objects.filter(
                    league=league, team_name=membership.team_name
                )

                count = drafted_teams.count()
                if count > 0:
                    # Update all matching records with both team_membership and user
                    drafted_teams.update(
                        team_membership=membership, user=membership.user
                    )
                    user_str = (
                        membership.user.username if membership.user else "Unclaimed"
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  - Updated {count} players for team '{membership.team_name}' (Owner: {user_str})"
                        )
                    )

            # Clear cache for this league
            cache_key = f"playoff_points_league_{league.id}_year_{league.league_year}"
            cache.delete(cache_key)
            self.stdout.write(f"  - Cleared cache for league")

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Done! Team memberships have been fixed."))
        self.stdout.write("=" * 60)
