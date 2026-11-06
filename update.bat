@echo off
REM 3point.app daily update for Windows (Task Scheduler fallback)
REM Scrapes the current season, rebuilds index.html, and pushes to GitHub.
REM Usage:  update.bat                 (current season)
REM         update.bat 2025-26 2026-27 (specific seasons)

cd /d "%~dp0"
echo ==== %date% %time% ==== >> update_log.txt

git pull --quiet >> update_log.txt 2>&1

if "%~1"=="" (
    python scrape_multi_season.py >> update_log.txt 2>&1
) else (
    python scrape_multi_season.py --seasons %* >> update_log.txt 2>&1
)
if errorlevel 1 (
    echo Scrape failed - site left unchanged. See update_log.txt >> update_log.txt
    exit /b 1
)

python create_multi_season_website.py >> update_log.txt 2>&1
if errorlevel 1 exit /b 1

git add nba_shooting_data_all_seasons.json metadata.json index.html
git diff --cached --quiet -- nba_shooting_data_all_seasons.json
if errorlevel 1 (
    git commit -m "Daily data update %date%" >> update_log.txt 2>&1
    git push >> update_log.txt 2>&1
) else (
    echo No new stats today. >> update_log.txt
    git reset --quiet
)
echo Done. >> update_log.txt
