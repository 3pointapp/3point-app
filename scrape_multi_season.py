"""
NBA 3-Point Shooting Stats Scraper - Multi-Season Version
Scrapes defender-distance 3PT data from NBA.com and calculates 3P%OE, 3PES, 3PAA,
plus career stats aggregated across every season.

Usage:
    python scrape_multi_season.py                      # daily update: re-scrape current season only
    python scrape_multi_season.py --seasons 2025-26 2026-27   # re-scrape specific seasons
    python scrape_multi_season.py --full               # re-scrape every season from 2013-14

Seasons that aren't re-scraped are reused from the existing
nba_shooting_data_all_seasons.json, so a daily run is ~4 API calls instead of ~56.
If any API call fails, the script exits with an error and leaves the JSON untouched,
so a bad day never wipes the site's data.
"""

from nba_api.stats.endpoints import LeagueDashPlayerPtShot
from collections import defaultdict
from datetime import datetime, timezone
import argparse
import json
import os
import sys
import time

import pandas as pd

DATA_FILE = 'nba_shooting_data_all_seasons.json'
META_FILE = 'metadata.json'

FIRST_SEASON_START = 2013  # tracking data begins 2013-14


def season_label(start_year):
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def current_season_start_year(today=None):
    """NBA season rolls over in October: Oct 2026 onward is 2026-27."""
    today = today or datetime.now()
    return today.year if today.month >= 10 else today.year - 1


def all_seasons(today=None):
    """Every season from 2013-14 through the current one, newest first."""
    last = current_season_start_year(today)
    return [season_label(y) for y in range(last, FIRST_SEASON_START - 1, -1)]


DEFENDER_DISTANCES = [
    {'range': '0-2 Feet - Very Tight', 'label': 'very_tight'},
    {'range': '2-4 Feet - Tight', 'label': 'tight'},
    {'range': '4-6 Feet - Open', 'label': 'open'},
    {'range': '6+ Feet - Wide Open', 'label': 'wide_open'}
]
LABELS = [d['label'] for d in DEFENDER_DISTANCES]

# NBA.com is picky about headers; these match a normal browser visit.
NBA_HEADERS = {
    'Host': 'stats.nba.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.nba.com/',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive',
}


def fetch_distance(season, distance, retries=4, timeout=60):
    """One API call with retries. Raises if every attempt fails."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            shot_data = LeagueDashPlayerPtShot(
                season=season,
                season_type_all_star='Regular Season',
                per_mode_simple='Totals',
                close_def_dist_range_nullable=distance['range'],
                headers=NBA_HEADERS,
                timeout=timeout
            )
            return shot_data.get_data_frames()[0]
        except Exception as e:
            last_error = e
            wait = 10 * attempt
            print(f"\n    attempt {attempt}/{retries} failed ({type(e).__name__}: {e}); retrying in {wait}s", end="")
            time.sleep(wait)
    raise RuntimeError(f"{season} / {distance['range']}: all {retries} attempts failed: {last_error}")


def scrape_season_data(season):
    """
    Scrapes NBA shooting stats for a single season.
    Raises on failure instead of silently filling a distance bucket with zeros
    (a missing bucket would corrupt every player's 3P%OE).
    """
    all_players = {}
    max_gp = 0  # most games played by any player ~= team games so far

    print(f"\nScraping {season} season...")
    print("=" * 60)

    for distance in DEFENDER_DISTANCES:
        print(f"  Scraping: {distance['range']}", end=" ")
        df = fetch_distance(season, distance)
        print(f"✓ ({len(df)} players)")
        if 'GP' in df.columns and len(df):
            max_gp = max(max_gp, int(pd.to_numeric(df['GP'], errors='coerce').fillna(0).max()))

        for _, row in df.iterrows():
            player_name = row['PLAYER_NAME']
            player_id = int(row['PLAYER_ID']) if 'PLAYER_ID' in row and pd.notna(row['PLAYER_ID']) else None
            team = row['PLAYER_LAST_TEAM_ABBREVIATION'] if 'PLAYER_LAST_TEAM_ABBREVIATION' in row else 'UNK'

            fg3m = row['FG3M'] if 'FG3M' in row and pd.notna(row['FG3M']) else 0
            fg3a = row['FG3A'] if 'FG3A' in row and pd.notna(row['FG3A']) else 0

            if player_name not in all_players:
                all_players[player_name] = {
                    'player': player_name,
                    'player_id': player_id,
                    'team': team,
                    **{f'{label}_3pm': 0 for label in LABELS},
                    **{f'{label}_3pa': 0 for label in LABELS},
                }

            all_players[player_name][f"{distance['label']}_3pm"] = int(fg3m)
            all_players[player_name][f"{distance['label']}_3pa"] = int(fg3a)

        time.sleep(2)  # be polite to the API

    return all_players, max_gp


def calculate_stats_for_players(all_players, season_label_str):
    """
    Calculate percentages, frequencies, 3P%OE, 3PES and 3PAA for players.
    (Unchanged math from the original version.)
    """
    league_totals = {f'{label}_{s}': 0 for label in LABELS for s in ('3pm', '3pa')}

    final_data = []
    for player_name, data in all_players.items():
        total_3pa = sum(data[f'{label}_3pa'] for label in LABELS)

        if total_3pa > 0:
            for label in LABELS:
                attempts = data[f'{label}_3pa']
                makes = data[f'{label}_3pm']
                data[f'{label}_3p_pct'] = round((makes / attempts) * 100, 1) if attempts > 0 else 0.0
                data[f'{label}_freq'] = round((attempts / total_3pa) * 100, 1)
                league_totals[f'{label}_3pm'] += makes
                league_totals[f'{label}_3pa'] += attempts

            data['total_3pa'] = total_3pa
            data['total_3pm'] = sum(data[f'{label}_3pm'] for label in LABELS)
            data['season'] = season_label_str
            final_data.append(data)

    league_averages = {}
    for label in LABELS:
        makes = league_totals[f'{label}_3pm']
        attempts = league_totals[f'{label}_3pa']
        league_averages[f'{label}_3p_pct'] = (makes / attempts) * 100 if attempts > 0 else 0.0

    for data in final_data:
        oe_total = 0.0
        for label in LABELS:
            contribution = (data[f'{label}_3p_pct'] - league_averages[f'{label}_3p_pct']) * (data[f'{label}_freq'] / 100)
            oe_total += contribution

        data['3p_pct_oe'] = round(oe_total, 2)

        # 3PES = [(3P%OE × 3PM) / (1 + 0.01 × 3PA)] / 10
        data['3pes'] = round(((oe_total * data['total_3pm']) / (1 + 0.01 * data['total_3pa'])) / 10, 2)

        # 3PAA = 3P%OE × 3PM
        data['3paa'] = round(oe_total * data['total_3pm'], 2)

    final_data.sort(key=lambda x: x['3p_pct_oe'], reverse=True)
    return final_data, league_averages


def calculate_career_stats(all_season_data):
    """Calculate career stats by aggregating every season's raw makes/attempts."""
    print("\n" + "=" * 60)
    print("Calculating career stats...")
    print("=" * 60)

    career_players = defaultdict(lambda: {
        'player': '',
        'player_id': None,
        'team': 'Multiple',
        **{f'{label}_3pm': 0 for label in LABELS},
        **{f'{label}_3pa': 0 for label in LABELS},
        'seasons_played': []
    })

    # Oldest season first, so the most recent player_id wins
    for season in sorted(all_season_data.keys()):
        for player_data in all_season_data[season]:
            player_name = player_data['player']
            cp = career_players[player_name]
            cp['player'] = player_name
            if player_data.get('player_id'):
                cp['player_id'] = player_data['player_id']
            for label in LABELS:
                cp[f'{label}_3pm'] += player_data[f'{label}_3pm']
                cp[f'{label}_3pa'] += player_data[f'{label}_3pa']
            cp['seasons_played'].append(season)

    seasons_by_player = {name: len(p['seasons_played']) for name, p in career_players.items()}
    career_data, _ = calculate_stats_for_players(dict(career_players), 'Career')

    for player in career_data:
        player['seasons_played'] = seasons_by_player[player['player']]
        player['season'] = 'Career'

    print(f"  ✓ Career stats calculated for {len(career_data)} players")
    return career_data


def load_existing():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data.pop('Career', None)  # always rebuilt from the seasons
    return data


def main():
    parser = argparse.ArgumentParser(description="Scrape NBA.com defender-distance 3PT data")
    parser.add_argument('--full', action='store_true', help='re-scrape every season since 2013-14')
    parser.add_argument('--seasons', nargs='+', help='specific seasons to re-scrape, e.g. 2025-26 2026-27')
    args = parser.parse_args()

    seasons = all_seasons()
    current = seasons[0]

    if args.full:
        to_scrape = seasons
    elif args.seasons:
        bad = [s for s in args.seasons if s not in seasons]
        if bad:
            sys.exit(f"Unknown season(s): {bad}. Valid: {seasons[-1]} through {current}")
        to_scrape = args.seasons
    else:
        to_scrape = [current]

    existing = load_existing()
    missing = [s for s in seasons if s not in existing and s not in to_scrape]
    if missing:
        print(f"Seasons not in the existing JSON will be scraped too: {missing}")
        to_scrape = to_scrape + missing

    print("\n" + "=" * 60)
    print("NBA 3P%OE Multi-Season Scraper")
    print("=" * 60)
    print(f"Re-scraping: {', '.join(to_scrape)}")
    print(f"Reusing from existing JSON: {len([s for s in seasons if s not in to_scrape])} seasons")

    all_season_data = {s: existing[s] for s in seasons if s in existing}
    old_meta = {}
    if os.path.exists(META_FILE):
        with open(META_FILE, 'r', encoding='utf-8') as f:
            old_meta = json.load(f)
    games_by_season = {}
    try:
        for season in to_scrape:
            players, max_gp = scrape_season_data(season)
            games_by_season[season] = max_gp
            player_data, _ = calculate_stats_for_players(players, season)
            if not player_data:
                # Preseason / no games yet: don't add an empty season to the site
                print(f"  - {season}: no 3PA yet, skipping")
                all_season_data.pop(season, None)
                continue
            all_season_data[season] = player_data
            print(f"  ✓ {season}: {len(player_data)} players with 3PA")
    except RuntimeError as e:
        print(f"\n✗ Scrape failed, existing data left untouched.\n  {e}")
        sys.exit(1)

    career_data = calculate_career_stats(all_season_data)

    # Career first, then newest season to oldest (same layout as before)
    combined = {'Career': career_data}
    for s in seasons:
        if s in all_season_data:
            combined[s] = all_season_data[s]

    tmp = DATA_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(combined, f, indent=2)
    os.replace(tmp, DATA_FILE)

    now = datetime.now(timezone.utc)
    latest = next(s for s in seasons if s in all_season_data)
    if latest in games_by_season:
        latest_games = games_by_season[latest]
    elif old_meta.get('latest_season') == latest:
        latest_games = old_meta.get('latest_season_team_games')
    else:
        latest_games = None
    with open(META_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_updated_utc': now.isoformat(timespec='seconds'),
            'seasons_scraped': to_scrape,
            'first_season': seasons[-1],
            'latest_season': latest,
            # used by the site to pro-rate the 82-3PA qualifier mid-season
            'latest_season_team_games': latest_games,
        }, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Saved {DATA_FILE} and {META_FILE}")
    print("=" * 60)

    print("\nTop 10 Career 3P%OE Leaders (min 250 3PM):")
    qualified = [p for p in career_data if p['total_3pm'] >= 250]
    for i, player in enumerate(qualified[:10]):
        print(f"{i+1}. {player['player']} - 3P%OE: {player['3p_pct_oe']:+.2f}% ({player['seasons_played']} seasons)")

    print("\nNext: run create_multi_season_website.py to rebuild index.html")


if __name__ == "__main__":
    main()
