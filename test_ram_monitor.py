"""
RAM usage monitor for the Django playoff-pool backend.

Uses Playwright to drive the React frontend while sampling the Django server
process's RSS (resident set size) after every page load and API call.

Setup (one-time):
    pip install playwright psutil
    playwright install chromium

Usage:
    1. In one terminal, start the Django server:
           pyenv activate espn-api-v3
           python manage.py runserver 8001

    2. In another terminal, run this script:
           pyenv activate espn-api-v3
           python test_ram_monitor.py [--league-id <id>] [--username <u> --password <p>]

       If --league-id is omitted the script picks the first league it finds.
       If --username / --password are omitted it tries the API unauthenticated
       (read-only endpoints still work).
"""

import argparse
import os
import sys
import time
import json
import subprocess
from datetime import datetime

try:
    import psutil
except ImportError:
    sys.exit("psutil not installed. Run: pip install psutil")

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    sys.exit("playwright not installed. Run: pip install playwright && playwright install chromium")


BASE_URL = "http://localhost:8001"
SAMPLE_WAIT_S = 1.5   # seconds to pause after navigation before sampling
REPEAT_PAGES = 5       # how many times to reload the expensive page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_django_pids() -> list[int]:
    """Return PIDs of processes that look like the Django dev server."""
    pids = []
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or [])
            if "manage.py" in cmdline and "runserver" in cmdline:
                pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return pids


def rss_mb(pids: list[int]) -> float:
    """Sum RSS (MB) across a list of PIDs (parent + reloader child)."""
    total = 0
    for pid in pids:
        try:
            p = psutil.Process(pid)
            total += p.memory_info().rss
            # Also count child processes (Django spawns a reloader)
            for child in p.children(recursive=True):
                try:
                    total += child.memory_info().rss
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return total / 1024 / 1024


def sample(label: str, pids: list[int], results: list[dict]) -> float:
    time.sleep(SAMPLE_WAIT_S)
    mb = rss_mb(pids)
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}]  {mb:7.1f} MB  {label}")
    results.append({"label": label, "mb": mb, "ts": ts})
    return mb


def wait_for_server(timeout=30):
    """Block until the Django dev server responds."""
    import urllib.request, urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/playoff-pool/", timeout=2)
            return True
        except Exception:
            time.sleep(1)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="RAM monitor for Django playoff-pool")
    parser.add_argument("--league-id", type=int, default=None)
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run browser headlessly (default: True)")
    parser.add_argument("--show-browser", action="store_true",
                        help="Show the browser window")
    args = parser.parse_args()
    headless = not args.show_browser

    # 1. Find Django server process
    pids = find_django_pids()
    if not pids:
        sys.exit(
            "Django dev server not found. Start it first:\n"
            "  pyenv activate espn-api-v3 && python manage.py runserver 8001"
        )
    print(f"Django server PID(s): {pids}")

    if not wait_for_server():
        sys.exit(f"Server at {BASE_URL} did not respond within 30 s")

    results: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        ctx = browser.new_context()
        page = ctx.new_page()

        # Silence console noise
        page.on("console", lambda m: None)

        print(f"\n{'='*60}")
        print("RAM USAGE MONITOR  (Django server RSS)")
        print(f"{'='*60}")

        # Baseline
        sample("baseline (server idle)", pids, results)

        # 2. Load the home page
        page.goto(f"{BASE_URL}/", wait_until="networkidle")
        sample("home page loaded", pids, results)

        # 3. Authenticate if credentials supplied
        token = None
        if args.username and args.password:
            response = page.request.post(
                f"{BASE_URL}/playoff-pool/auth/login/",
                data=json.dumps({"username": args.username, "password": args.password}),
                headers={"Content-Type": "application/json"},
            )
            if response.ok:
                token = response.json().get("token")
                print(f"  Logged in as {args.username}, token: {token[:8]}...")
            else:
                print(f"  WARNING: login failed ({response.status}), continuing unauthenticated")

        auth_headers = {"Authorization": f"Token {token}"} if token else {}

        # 4. Discover league ID
        league_id = args.league_id
        if league_id is None:
            resp = page.request.get(
                f"{BASE_URL}/playoff-pool/leagues/",
                headers=auth_headers,
            )
            if resp.ok:
                leagues = resp.json()
                if isinstance(leagues, list) and leagues:
                    league_id = leagues[0]["id"]
                elif isinstance(leagues, dict) and leagues.get("results"):
                    league_id = leagues["results"][0]["id"]
            if league_id is None:
                print("  WARNING: could not discover a league ID — skipping league pages")
            else:
                print(f"  Using league_id={league_id}")

        sample("after auth / league discovery", pids, results)

        # 5. Hit each API endpoint directly (simulates backend work without React overhead)
        if league_id:
            print(f"\n--- Direct API calls (league {league_id}) ---")

            page.request.get(f"{BASE_URL}/playoff-pool/leagues/{league_id}/", headers=auth_headers)
            sample("GET /leagues/{id}/", pids, results)

            page.request.get(f"{BASE_URL}/playoff-pool/leagues/{league_id}/members/", headers=auth_headers)
            sample("GET /leagues/{id}/members/", pids, results)

            page.request.get(f"{BASE_URL}/playoff-pool/leagues/{league_id}/playoff_stats/", headers=auth_headers)
            sample("GET /leagues/{id}/playoff_stats/ [1st — may build cache]", pids, results)

            page.request.get(f"{BASE_URL}/playoff-pool/leagues/{league_id}/drafted_teams/", headers=auth_headers)
            sample("GET /leagues/{id}/drafted_teams/ [1st]", pids, results)

        # 6. Navigate the React UI pages
        print(f"\n--- React page navigations ---")

        page.goto(f"{BASE_URL}/playoff-pool/", wait_until="networkidle")
        sample("React: /playoff-pool/ (home)", pids, results)

        if league_id:
            page.goto(f"{BASE_URL}/playoff-pool/league/{league_id}", wait_until="networkidle")
            sample(f"React: league detail", pids, results)

            page.goto(f"{BASE_URL}/playoff-pool/league/{league_id}/drafted-teams", wait_until="networkidle")
            sample(f"React: drafted-teams [1st load]", pids, results)

        # 7. Reload the expensive page several times to observe memory growth (or lack of it)
        if league_id:
            print(f"\n--- Repeat reloads of drafted-teams (testing for leaks) ---")
            for i in range(2, REPEAT_PAGES + 1):
                page.goto(f"{BASE_URL}/playoff-pool/league/{league_id}/drafted-teams", wait_until="networkidle")
                sample(f"React: drafted-teams [reload #{i}]", pids, results)

        # 8. Repeat the API calls to confirm cache is being served from DB
        if league_id:
            print(f"\n--- Repeat API calls (should be cheap DB reads now) ---")
            for i in range(2, 4):
                page.request.get(f"{BASE_URL}/playoff-pool/leagues/{league_id}/playoff_stats/", headers=auth_headers)
                sample(f"GET playoff_stats [call #{i}]", pids, results)

        browser.close()

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    baseline = results[0]["mb"] if results else 0
    peak = max(r["mb"] for r in results)
    final = results[-1]["mb"] if results else 0

    print(f"  Baseline  : {baseline:7.1f} MB")
    print(f"  Peak      : {peak:7.1f} MB  (+{peak - baseline:.1f} MB above baseline)")
    print(f"  Final     : {final:7.1f} MB  (+{final - baseline:.1f} MB above baseline)")
    print()

    # Detect growth across repeated reloads
    reload_results = [r for r in results if "reload #" in r["label"]]
    if len(reload_results) >= 2:
        growth = reload_results[-1]["mb"] - reload_results[0]["mb"]
        per_reload = growth / (len(reload_results) - 1)
        print(f"  Memory growth across {len(reload_results)} repeated reloads:")
        print(f"    Total : {growth:+.1f} MB")
        print(f"    Per reload : {per_reload:+.1f} MB")
        if abs(per_reload) < 5:
            print("    Result: STABLE (< 5 MB per reload) ✓")
        else:
            print("    Result: GROWING — possible leak ✗")

    print()

    # Save full results to JSON for further analysis
    out_path = "ram_monitor_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Full results saved to {out_path}")


if __name__ == "__main__":
    main()
