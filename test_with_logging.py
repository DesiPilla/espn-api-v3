import os
import django
import logging
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.doritostats.settings')
django.setup()

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('backend.playoff_pool.cache_utils')
logger.setLevel(logging.DEBUG)

from backend.playoff_pool.models import League
from backend.playoff_pool.cache_utils import refresh_league_cache

league = League.objects.get(id=20)
print(f"Refreshing cache for league {league.id}...")
refresh_league_cache(league)
print("Done!")
