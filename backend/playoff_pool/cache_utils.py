"""
Cache utilities for playoff pool application.
Handles pre-computing and storing fantasy points in PostgreSQL.
"""
import gc
import logging
import pandas as pd
import pyarrow as pa
import nflreadpy as nfl
from django.db import transaction
from django.utils import timezone
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache most_recent_game at module level (refreshes per-process, not per-request)
_GAME_CACHE = {}
_GAME_CACHE_TTL = 1 * 60  # 1 minute


def should_refresh_cache(league):
    """
    Fast heuristic: Compare cached game timestamp to current most recent game.
    Cost: 1 DB query + 1 lightweight API call (cached in-memory)

    Args:
        league: League model instance

    Returns:
        tuple: (needs_refresh: bool, reason: str)
    """
    from .scoring import get_most_recent_game
    from .models import CachedPlayerStats

    year = league.league_year

    # Step 1: Check if any cached stats exist for this league
    cached_stat = CachedPlayerStats.objects.filter(league=league).first()

    if not cached_stat:
        return True, "No cache exists for this league"

    # Step 2: Get current most recent game (with in-memory caching)
    try:
        cache_key = f"game_{year}"
        now = datetime.now()

        # Check in-memory cache first
        if cache_key in _GAME_CACHE:
            cached_data, cached_time = _GAME_CACHE[cache_key]
            if (now - cached_time).total_seconds() < _GAME_CACHE_TTL:
                current_game_info = cached_data
            else:
                # Cache expired, refresh it
                current_game_info = get_most_recent_game(year)
                _GAME_CACHE[cache_key] = (current_game_info, now)
        else:
            # Not in cache, fetch and cache it
            current_game_info = get_most_recent_game(year)
            _GAME_CACHE[cache_key] = (current_game_info, now)

        current_game_id = current_game_info["game_id"]
        current_gametime = pd.to_datetime(current_game_info["gametime"])
    except Exception as e:
        logger.warning(f"Could not get most recent game: {e}")
        return False, "Could not check for new games"

    # Step 3: Compare timestamps
    # All stats for this league should have the same most_recent_game_id
    cached_game_id = cached_stat.most_recent_game_id
    cached_gametime = cached_stat.most_recent_gametime

    logger.info(
        f"Cache check for league {league.id}: "
        f"Most recent game: {current_game_id} ({current_gametime}), "
        f"Cached game: {cached_game_id} ({cached_gametime})"
    )

    if cached_game_id != current_game_id:
        logger.info(
            f"Cache refresh NEEDED for league {league.id}: "
            f"New game detected: {current_game_id} (cached: {cached_game_id})"
        )
        return True, f"New game detected: {current_game_id} (cached: {cached_game_id})"

    logger.info(f"Cache refresh NOT needed for league {league.id}: Cache is up to date")
    return False, "Cache is up to date"


def refresh_league_cache(league):
    """
    Rebuild cache for a specific league using its custom scoring.
    Also updates global CachedPlayers table as needed.

    Args:
        league: League model instance
    """
    from .scoring import (
        get_most_recent_game,
        get_league_scoring_settings,
        SCORING_MULTIPLIERS,
    )
    from .models import CachedPlayers, CachedPlayerStats, DraftedTeam
    from .players import get_defense_stats, get_schedule

    year = league.league_year

    logger.info(f"Starting cache refresh for league {league.id} ({league.name})")

    with transaction.atomic():
        # Step 1: Get most recent game metadata
        et_tz = pytz.timezone("America/New_York")
        try:
            most_recent_game_info = get_most_recent_game(year)
            most_recent_game_id = most_recent_game_info["game_id"]
            # Convert to timezone-aware datetime
            most_recent_gametime = pd.to_datetime(most_recent_game_info["gametime"])
            if most_recent_gametime.tzinfo is None:
                most_recent_gametime = et_tz.localize(most_recent_gametime)
        except Exception as e:
            # No completed games yet — build a placeholder cache so subsequent
            # requests serve from the DB rather than loading DataFrames every time.
            logger.info(
                f"No completed games found for year {year}, building placeholder cache: {e}"
            )
            most_recent_game_id = f"{year}_NO_GAME"
            most_recent_gametime = et_tz.localize(pd.Timestamp("2000-01-01"))

        # Step 2: Load NFL playoff data — filter immediately to keep only what's needed.
        # nfl.load_player_stats() returns all seasons/weeks (~17k rows, 50+ columns).
        # We only need POST weeks and the columns used in scoring + player identity.
        logger.debug(f"Loading NFL playoff data for year {year}")

        _player_id_cols = [
            "player_display_name", "position", "team",
            "season", "week", "season_type", "opponent",
        ]
        _raw_player = nfl.load_player_stats([year]).to_pandas()
        _scoring_cols = list(SCORING_MULTIPLIERS.keys())
        _player_keep = [
            c for c in (_player_id_cols + _scoring_cols)
            if c in _raw_player.columns
        ]
        weekly_stats = (
            _raw_player[_raw_player["season_type"] == "POST"][_player_keep]
            .copy()
        )
        del _raw_player
        gc.collect()
        pa.default_memory_pool().release_unused()
        logger.debug(f"Player stats: {len(weekly_stats)} POST rows retained")

        defense_stats = get_defense_stats(year)

        # Add player_display_name to defense stats to match regular player stats format
        defense_stats["player_display_name"] = defense_stats["full_name"]

        # Drop team_score and opponent_score from defense stats to avoid merge conflicts
        # (we'll add them back from schedule for all players together)
        defense_stats = defense_stats.drop(
            columns=["team_score", "opponent_score"], errors="ignore"
        )

        # Concat: player rows carry player-scoring columns; defense rows carry defense-scoring
        # columns. Mismatched columns become NaN — the scoring loop handles this with fillna(0).
        weekly_stats = pd.concat([weekly_stats, defense_stats], sort=False)
        del defense_stats  # Free memory: no longer needed after concat
        weekly_stats = weekly_stats[weekly_stats["season_type"] == "POST"]

        if weekly_stats.empty:
            logger.info(
                f"No playoff stats yet for year {year} — "
                "placeholder cache will be built with 0-point entries"
            )

        # Step 3 (pre-filter): Narrow weekly_stats to only this league's drafted players
        # before the schedule merge. Reduces from ~1,700 rows (all 14 playoff-team players)
        # to ~50-100 rows, making all downstream operations much cheaper.
        drafted_players = DraftedTeam.objects.filter(league=league)
        if not drafted_players.exists():
            error_msg = f"No drafted players found for league {league.id}"
            logger.warning(error_msg)
            raise Exception(error_msg)

        if not weekly_stats.empty:
            _drafted_filter = pd.DataFrame([
                {
                    "player_display_name": dp.player_name,
                    "position": dp.position,
                    "team": dp.nfl_team,
                }
                for dp in drafted_players
            ])
            weekly_stats = weekly_stats.merge(
                _drafted_filter,
                on=["player_display_name", "position", "team"],
                how="inner",
            )
            del _drafted_filter
            logger.debug(f"Stats filtered to drafted players: {len(weekly_stats)} rows")

        if not weekly_stats.empty:
            # Step 3a: Load schedule and calculate elimination status
            logger.debug(
                f"Loading schedule and calculating elimination status for year {year}"
            )
            schedule = get_schedule(year)

            # Filter schedule to only playoff weeks to match with weekly_stats
            schedule_playoff = schedule[schedule["week"].isin([19, 20, 21, 22])]

            # Merge schedule with weekly stats to get team scores
            # Use left join to keep all player stats even if schedule data doesn't exist yet
            weekly_stats = weekly_stats.merge(
                schedule_playoff[
                    ["season", "week", "team", "team_score", "opponent_score"]
                ],
                on=["season", "week", "team"],
                how="left",
            )

            # Ensure columns exist even if merge produced no matches
            if "team_score" not in weekly_stats.columns:
                weekly_stats["team_score"] = pd.NA
            if "opponent_score" not in weekly_stats.columns:
                weekly_stats["opponent_score"] = pd.NA

            # Calculate elimination: player is eliminated if their team lost
            # NaN comparisons evaluate to False, so no-game-data defaults to not eliminated
            weekly_stats["is_eliminated"] = (
                weekly_stats["team_score"] < weekly_stats["opponent_score"]
            ).fillna(False)

        # Step 3b: Get league's custom scoring settings
        scoring_settings = get_league_scoring_settings(league)

        # Step 4: Delete existing cache for this league only
        # (drafted_players already queried and validated above)
        deleted_count = CachedPlayerStats.objects.filter(league=league).delete()[0]
        logger.debug(
            f"Deleted {deleted_count} old cache entries for league {league.id}"
        )

        # Step 6: Bulk update/create all CachedPlayers entries first (single query)
        week_to_game_type = {19: "WC", 20: "DIV", 21: "CON", 22: "SB"}

        # Pre-fetch existing cached players to avoid N queries
        existing_cached = {
            (cp.gsis_id, cp.year): cp for cp in CachedPlayers.objects.filter(year=year)
        }

        cached_players_to_create = []
        cached_players_to_update = []
        now = timezone.now()

        for drafted_player in drafted_players:
            key = (drafted_player.gsis_id, year)
            if key in existing_cached:
                # Update existing
                cp = existing_cached[key]
                cp.player_name = drafted_player.player_name
                cp.position = drafted_player.position
                cp.nfl_team = drafted_player.nfl_team
                cp.most_recent_game_id = most_recent_game_id
                cp.most_recent_gametime = most_recent_gametime
                cp.last_updated = now
                cached_players_to_update.append(cp)
            else:
                # Create new
                cp = CachedPlayers(
                    gsis_id=drafted_player.gsis_id,
                    year=year,
                    player_name=drafted_player.player_name,
                    position=drafted_player.position,
                    nfl_team=drafted_player.nfl_team,
                    most_recent_game_id=most_recent_game_id,
                    most_recent_gametime=most_recent_gametime,
                    last_updated=now,
                )
                cached_players_to_create.append(cp)
                existing_cached[key] = cp

        # Bulk operations
        if cached_players_to_create:
            CachedPlayers.objects.bulk_create(cached_players_to_create, batch_size=100)
        if cached_players_to_update:
            CachedPlayers.objects.bulk_update(
                cached_players_to_update,
                [
                    "player_name",
                    "position",
                    "nfl_team",
                    "most_recent_game_id",
                    "most_recent_gametime",
                    "last_updated",
                ],
                batch_size=100,
            )

        logger.debug(
            f"Updated {len(cached_players_to_update)} and created {len(cached_players_to_create)} CachedPlayers"
        )

        # Step 7: Build stats entries from playoff records (skipped if no playoff data yet)
        stats_bulk = []
        players_with_stats = set()  # Track which players have stats

        if not weekly_stats.empty:
            # Filter stats to only playoff weeks
            playoff_weeks = list(week_to_game_type.keys())
            weekly_stats_filtered = weekly_stats[
                weekly_stats["week"].isin(playoff_weeks)
            ].copy()

            # Pre-calculate fantasy points for all rows (vectorized using numpy operations)
            logger.debug("Calculating fantasy points for all rows...")
            weekly_stats_filtered["fantasy_points"] = 0.0

            # Vectorized point calculation - much faster than apply()
            for stat, config in scoring_settings.items():
                if isinstance(config, dict):
                    multiplier = config.get("default_value", 0)
                else:
                    multiplier = config

                if stat in weekly_stats_filtered.columns and pd.notna(multiplier):
                    weekly_stats_filtered["fantasy_points"] += (
                        weekly_stats_filtered[stat].fillna(0) * multiplier
                    )

            # Convert to dict records for faster iteration (avoids pandas overhead)
            stats_records = weekly_stats_filtered.to_dict("records")

            # Debug: Check if is_eliminated is in the data
            if stats_records:
                sample_record = stats_records[0]
                logger.debug(f"Sample record keys: {list(sample_record.keys())}")
                if "is_eliminated" in sample_record:
                    logger.debug(
                        f"is_eliminated present in records: {sample_record.get('is_eliminated')}"
                    )
                else:
                    logger.warning("is_eliminated NOT found in records!")

            # Build lookup dict for faster matching
            logger.debug("Building player stat entries...")
            drafted_lookup = {
                (dp.player_name, dp.position, dp.nfl_team): dp for dp in drafted_players
            }

            for record in stats_records:
                key = (
                    record.get("player_display_name"),
                    record.get("position"),
                    record.get("team"),
                )

                if key not in drafted_lookup:
                    continue

                drafted_player = drafted_lookup[key]
                cached_player = existing_cached.get((drafted_player.gsis_id, year))

                if not cached_player:
                    continue

                # Track that this player has stats
                players_with_stats.add(drafted_player.gsis_id)

                week = record["week"]
                game_type = week_to_game_type[week]
                game_id = f"{record['season']}_{week}_{record.get('opponent', 'UNK')}"

                stats_bulk.append(
                    CachedPlayerStats(
                        league=league,
                        cached_player=cached_player,
                        week=week,
                        game_type=game_type,
                        game_id=game_id,
                        most_recent_game_id=most_recent_game_id,
                        most_recent_gametime=most_recent_gametime,
                        fantasy_points=record["fantasy_points"],
                        is_eliminated=bool(record.get("is_eliminated", False)),
                    )
                )

        # Free large DataFrames now that stats_bulk is built — no longer needed
        weekly_stats = None
        if "weekly_stats_filtered" in dir():
            weekly_stats_filtered = None
        if "stats_records" in dir():
            stats_records = None
        if "schedule" in dir():
            schedule = None

        # Step 8: Create placeholder entries for players without stats yet (e.g., bye week)
        logger.debug("Creating placeholder entries for players without stats...")
        for drafted_player in drafted_players:
            if drafted_player.gsis_id not in players_with_stats:
                cached_player = existing_cached.get((drafted_player.gsis_id, year))
                if cached_player:
                    # Create a placeholder entry with 0 points for the first playoff week
                    stats_bulk.append(
                        CachedPlayerStats(
                            league=league,
                            cached_player=cached_player,
                            week=19,  # Wildcard week
                            game_type="WC",
                            game_id=f"{year}_19_BYE",
                            most_recent_game_id=most_recent_game_id,
                            most_recent_gametime=most_recent_gametime,
                            fantasy_points=0.0,
                            is_eliminated=False,  # Not eliminated if they haven't played
                        )
                    )

        # Count unique players
        players_cached = len(set(stat.cached_player_id for stat in stats_bulk))

        # Single bulk create for ALL stats
        logger.debug(f"Bulk creating {len(stats_bulk)} stat entries...")
        if stats_bulk:
            CachedPlayerStats.objects.bulk_create(stats_bulk, batch_size=1000)

        stats_created = len(stats_bulk)

        logger.info(
            f"Cache refresh complete for league {league.id} ({league.name}): "
            f"{players_cached} players cached, {stats_created} game stats created, "
            f"most recent game: {most_recent_game_id}"
        )

    # Return pyarrow's memory pool back to the OS.
    # pyarrow's allocator never returns freed buffers to the OS on its own,
    # so after loading large DataFrames the process RSS stays elevated forever.
    # release_unused() is the only way to reclaim that RAM.
    gc.collect()
    try:
        pa.default_memory_pool().release_unused()
        logger.debug("Released pyarrow memory pool after cache refresh")
    except Exception:
        pass
