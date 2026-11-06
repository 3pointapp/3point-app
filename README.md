# 3point.app

NBA 3-point shooting analytics by defender distance (3PES, 3P%OE, 3PAA).
Live: https://3pointapp.github.io/3point-app/

## Files
- `scrape_multi_season.py` - pulls NBA.com defender-distance data, computes metrics, writes `nba_shooting_data_all_seasons.json` + `metadata.json`
- `create_multi_season_website.py` - builds `index.html` from the JSON (data is embedded in the page)
- `.github/workflows/daily-update.yml` - runs both every morning Oct-Apr and pushes the result
- `update.bat` - same thing for Windows Task Scheduler, if NBA.com blocks GitHub's servers

## Commands
    pip install -r requirements.txt
    python scrape_multi_season.py                         # current season only (daily)
    python scrape_multi_season.py --seasons 2025-26 2026-27  # specific seasons
    python scrape_multi_season.py --full                  # everything since 2013-14
    python create_multi_season_website.py                 # rebuild index.html

New seasons are picked up automatically each October. If a scrape fails, the data is left untouched.
