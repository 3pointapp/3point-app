"""
Create multi-season website with season selector
"""
import json

print("Creating multi-season NBA stats website...")

# Read the multi-season data
try:
    with open('nba_shooting_data_all_seasons.json', 'r') as f:
        all_data = json.load(f)
    print(f"✓ Loaded data for {len(all_data)} seasons")
except FileNotFoundError:
    print("✗ Error: nba_shooting_data_all_seasons.json not found!")
    print("Run scrape_multi_season.py first!")
    exit(1)

import os
from datetime import datetime, timezone
meta = {}
if os.path.exists('metadata.json'):
    with open('metadata.json', 'r') as f:
        meta = json.load(f)
if 'last_updated_utc' in meta:
    last_updated_iso = meta['last_updated_utc']
else:
    # Fall back to the data file's modified time
    last_updated_iso = datetime.fromtimestamp(os.path.getmtime('nba_shooting_data_all_seasons.json'), timezone.utc).isoformat(timespec='seconds')

season_keys = sorted(k for k in all_data if k != 'Career')
first_season, latest_season = season_keys[0], season_keys[-1]
num_seasons = len(season_keys)
latest_year = int(latest_season[:4])
# In-progress season: qualifier is pro-rated at 1 3PA per team game (82 over a full season)
latest_games = meta.get('latest_season_team_games') if meta.get('latest_season') == latest_season else None
latest_qual = min(82, int(latest_games)) if latest_games else 82
print(f"✓ {latest_season} qualifier: {latest_qual} 3PA")
print(f"✓ Seasons {first_season} through {latest_season} ({num_seasons}); last updated {last_updated_iso}")

# Create the HTML with season selector
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-1WRGMV6T9R"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-1WRGMV6T9R');
    </script>
    
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3point.app - Advanced 3-Point Shooting Analytics | NBA Stats by Defender Distance</title>
    <meta name="description" content="Advanced NBA 3-point shooting statistics with defender distance breakdown. Featuring 3PES, 3P%OE, and 3PAA metrics for every player since 2013.">
    <link rel="icon" type="image/svg+xml" href="favicon.svg">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; color: #333; }
        
        /* Logo and Header */
        .site-header { text-align: center; margin-bottom: 30px; padding: 40px 0 30px 0; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .logo-container { margin-bottom: 20px; }
        .logo-icon { width: 100px; height: 100px; margin: 0 auto; position: relative; background-color: white; border-radius: 50%; padding: 15px; }
        .arc { position: absolute; width: 100%; height: 50%; border: 4px solid; border-bottom: none; border-radius: 100% 100% 0 0; left: 0; }
        .arc-1 { width: 100%; height: 100%; border-color: #002FA7; opacity: 1; bottom: 0; }
        .arc-2 { width: 80%; height: 80%; border-color: #0051D5; opacity: 0.85; left: 10%; bottom: 0; }
        .arc-3 { width: 60%; height: 60%; border-color: #2B7FE8; opacity: 0.7; left: 20%; bottom: 0; }
        .arc-4 { width: 40%; height: 40%; border-color: #6BA5F5; opacity: 0.55; left: 30%; bottom: 0; }
        .site-title { font-size: 42px; font-weight: bold; margin: 15px 0 8px 0; letter-spacing: -1px; color: #1a365d; }
        .site-tagline { font-size: 15px; color: #64748b; font-weight: normal; letter-spacing: 0.3px; }
        
        .container { max-width: 1600px; margin: 0 auto; background-color: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { font-size: 24px; margin-bottom: 10px; color: #1a1a1a; }
        .subtitle { font-size: 14px; color: #666; margin-bottom: 25px; }
        .controls { margin-bottom: 20px; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }
        .controls label { font-size: 14px; font-weight: bold; }
        .controls input, .controls select { padding: 6px 10px; border: 1px solid #ccc; font-size: 14px; }
        .season-selector { padding: 8px 12px; font-size: 15px; font-weight: bold; background-color: #fff9c4; border: 2px solid #f9a825; }
        .table-wrapper { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; white-space: nowrap; }
        th { background-color: #f0f0f0; padding: 10px 8px; text-align: left; border-bottom: 2px solid #ddd; cursor: pointer; user-select: none; position: sticky; top: 0; z-index: 10; }
        th:hover { background-color: #e5e5e5; }
        th.sortable::after { content: ' ↕'; font-size: 12px; color: #999; }
        th.sort-asc::after { content: ' ↑'; color: #333; }
        th.sort-desc::after { content: ' ↓'; color: #333; }
        .group-header { background-color: #e0e0e0; font-weight: bold; text-align: center; padding: 8px; border-right: 2px solid #ccc; }
        .very-tight { background-color: #ffebee; }
        .tight { background-color: #fff3e0; }
        .open { background-color: #e8f5e9; }
        .wide-open { background-color: #e3f2fd; }
        td { padding: 8px; border-bottom: 1px solid #eee; border-right: 1px solid #f5f5f5; }
        tr:hover { background-color: #f9f9f9; }
        .rank { color: #666; font-weight: bold; }
        .player-name { font-weight: bold; position: sticky; left: 0; background-color: white; z-index: 5; }
        tr:hover .player-name { background-color: #f9f9f9; }
        .stat-value { text-align: right; }
        .pct { color: #2196F3; }
        .freq { color: #9C27B0; font-size: 12px; }
        .footer { margin-top: 20px; font-size: 12px; color: #999; text-align: center; }
        .legend { margin-bottom: 15px; font-size: 12px; display: flex; gap: 20px; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 5px; }
        .legend-box { width: 20px; height: 15px; border: 1px solid #ccc; }
        
        /* Main Navigation Tabs */
        .main-nav { display: flex; gap: 0; margin: 20px 0; border-bottom: 3px solid #2196F3; }
        .main-tab { padding: 15px 30px; background-color: #f5f5f5; border: none; border-top-left-radius: 8px; border-top-right-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.3s; color: #666; }
        .main-tab:hover { background-color: #e0e0e0; }
        .main-tab.active { background-color: #2196F3; color: white; }
        .main-view { display: none; }
        .main-view.active { display: block; }
        
        /* Player Photo */
        .player-photo { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle; border: 2px solid #ddd; }
        .player-photo-placeholder { width: 40px; height: 40px; border-radius: 50%; background-color: #e0e0e0; display: inline-block; margin-right: 10px; vertical-align: middle; }
        .player-cell { display: flex; align-items: center; }
        
        /* Visualization Styles */
        .viz-container { background-color: #fafafa; padding: 20px; margin-bottom: 30px; border-radius: 8px; }
        .viz-container h2 { font-size: 20px; margin-bottom: 15px; color: #1a1a1a; }
        .viz-tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        .viz-tab { padding: 10px 20px; background-color: white; border: 2px solid #ddd; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; transition: all 0.3s; }
        .viz-tab:hover { background-color: #f0f0f0; }
        .viz-tab.active { background-color: #2196F3; color: white; border-color: #2196F3; }
        .viz-panel { display: none; background-color: white; padding: 20px; border-radius: 5px; min-height: 400px; }
        .viz-panel.active { display: block; }
        canvas { max-width: 100%; height: auto; }
        
        /* Player Filter Badges */
        .player-badge { background-color: #2196F3; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; display: inline-flex; align-items: center; gap: 5px; }
        .player-badge button { background: none; border: none; color: white; cursor: pointer; font-weight: bold; }
        
        /* Best 3PES Table */
        .best3pes-table { width: 100%; border-collapse: collapse; font-size: 14px; }
        .best3pes-table th { background-color: #f0f0f0; padding: 12px 8px; text-align: left; border-bottom: 2px solid #ddd; position: sticky; top: 0; }
        .best3pes-table td { padding: 10px 8px; border-bottom: 1px solid #eee; }
        .best3pes-table tr:hover { background-color: #f9f9f9; }
        .rank-col { width: 40px; text-align: center; font-weight: bold; color: #666; }
        .player-col { min-width: 200px; }
        .stat-col { text-align: right; min-width: 80px; }
        .bar-viz { height: 20px; background: linear-gradient(90deg, #2196F3 0%, #2196F3 var(--width), #e0e0e0 var(--width)); border-radius: 3px; position: relative; }
        .bar-label { position: absolute; right: 5px; top: 50%; transform: translateY(-50%); font-size: 11px; font-weight: bold; color: #333; }
        
        /* Visualization Info Boxes */
        .viz-info { background-color: #f0f8ff; border-left: 4px solid #2196F3; padding: 12px; margin-top: 15px; font-size: 13px; color: #555; border-radius: 4px; }
        .viz-info strong { color: #2196F3; }
        
        /* Footer */
        .site-footer { margin-top: 40px; padding: 30px; background-color: #1a365d; color: white; text-align: center; border-radius: 8px; }
        .site-footer a { color: #FF6B35; text-decoration: none; }
        .site-footer a:hover { text-decoration: underline; }
        .footer-links { margin: 15px 0; }
        .footer-links a { margin: 0 15px; }
        
        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
            body { padding: 10px; }
            
            /* Header adjustments */
            .site-header { padding: 25px 15px; }
            .logo-icon { width: 70px; height: 70px; }
            .site-title { font-size: 28px; }
            .site-tagline { font-size: 12px; }
            
            /* Container */
            .container { padding: 15px; }
            h1 { font-size: 20px; }
            .subtitle { font-size: 12px; }
            
            /* Main navigation */
            .main-nav { flex-direction: column; gap: 8px; }
            .main-tab { width: 100%; padding: 12px; font-size: 14px; }
            
            /* Hide Visualizations tab on mobile - too complex for small screens */
            .main-tab:nth-child(2) { display: none; }
            
            /* About page mobile styles */
            #about-view h1 { font-size: 24px !important; }
            #about-view h2 { font-size: 20px !important; }
            #about-view h3 { font-size: 16px !important; }
            #about-view p, #about-view li { font-size: 14px !important; }
            #about-view section { margin-bottom: 30px !important; }
            #about-view div[style*="padding: 20px"] { padding: 15px !important; }
            
            /* Show message if someone tries to access visualizations */
            #visualizations-view::before {
                content: 'Interactive charts are best viewed on desktop. View the Best 3PES Seasons table below, or use the Table View and Player Profile tabs for mobile-optimized data.';
                display: block;
                padding: 20px;
                background: #f0f8ff;
                border: 2px solid #2196F3;
                border-radius: 8px;
                color: #333;
                font-size: 13px;
                text-align: center;
                margin-bottom: 20px;
            }
            
            /* Hide chart controls and non-Best3PES viz on mobile */
            #visualizations-view .controls,
            #visualizations-view .viz-tabs,
            #scatter-viz,
            #metrics-viz,
            #efficiency-viz,
            #cumulative-viz {
                display: none !important;
            }
            
            /* Keep Best 3PES visible */
            #best3pes-viz {
                display: block !important;
            }
            
            /* Controls */
            .controls { flex-direction: column; gap: 10px; align-items: stretch; }
            .controls > div { width: 100%; }
            .controls input, .controls select { width: 100%; }
            .season-selector { font-size: 14px; }
            
            /* CRITICAL: Match all table fonts */
            table { 
                font-size: 10px; 
                min-width: 1200px; /* Force horizontal scroll */
            }
            th, td { padding: 8px 4px; font-size: 10px !important; }
            .freq { font-size: 10px !important; }
            
            /* Make player column narrower on mobile */
            .player-name {
                max-width: 120px !important;
                min-width: 120px !important;
            }
            .player-photo { width: 25px; height: 25px; }
            .player-cell { gap: 6px; }
            .player-cell span { 
                font-size: 10px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }
            
            /* Add scroll indicator */
            .table-wrapper::after {
                content: '← Swipe to see more →';
                display: block;
                text-align: center;
                padding: 8px;
                background: #f0f8ff;
                color: #2196F3;
                font-size: 11px;
                border-top: 1px solid #ddd;
            }
            
            /* Visualizations - CRITICAL FIXES */
            .viz-tabs { 
                flex-wrap: wrap; 
                gap: 5px;
                overflow-x: auto;
            }
            .viz-tab { 
                font-size: 11px; 
                padding: 8px 10px; 
                white-space: nowrap;
                flex: 0 0 auto;
            }
            
            /* Force charts to be responsive with proper aspect ratio */
            canvas { 
                max-width: 100% !important; 
                height: auto !important;
                min-height: 300px !important; /* Reduced from 350px */
            }
            
            /* Chart containers */
            .viz-panel {
                min-height: 350px; /* Reduced from 400px */
                width: 100%;
            }
            
            .viz-info { font-size: 11px; padding: 10px; }
            
            /* Best 3PES Table - MUCH NARROWER COLUMNS */
            .best3pes-table { 
                font-size: 8px !important;
                width: 100%;
                table-layout: fixed;
            }
            .best3pes-table th,
            .best3pes-table td { 
                padding: 3px 1px !important;
                white-space: nowrap;
                overflow: hidden;
            }
            .best3pes-table img { 
                width: 18px !important; 
                height: 18px !important; 
            }
            .best3pes-table .rank-col {
                width: 20px !important;
            }
            .best3pes-table .player-col {
                width: 70px !important;
                font-size: 7px;
                text-overflow: ellipsis;
            }
            .best3pes-table .stat-col {
                width: 35px !important;
            }
            /* Make the 3PES bar viz column even narrower */
            .best3pes-table td:last-child {
                width: 50px !important;
            }
            #best3pesTable {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }
            
            /* Player Profile - CRITICAL FIXES */
            #playerProfileSelect { width: 100%; font-size: 14px; }
            #playerHeader { 
                flex-direction: column; 
                text-align: center; 
                padding: 15px; 
            }
            #playerHeader img { 
                width: 80px !important; 
                height: 80px !important; 
            }
            #playerHeader > div { 
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 8px; 
                font-size: 12px; 
            }
            
            /* Player profile charts - stack vertically with BETTER aspect ratio */
            #playerProfileContent > div:nth-child(2) { 
                grid-template-columns: 1fr !important;
                gap: 20px;
            }
            
            /* Make player profile charts SHORTER with better proportions */
            #playerProfileContent canvas {
                width: 100% !important;
                height: 280px !important; /* Reduced from 350px */
                max-width: 100% !important;
            }
            
            /* Player season table */
            #playerSeasonTable {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
            }
            #playerSeasonTable table {
                font-size: 9px;
                min-width: 600px;
            }
            
            /* Similar players - 2 columns on mobile */
            #similarPlayersGrid { 
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 10px;
            }
            #similarPlayersGrid > div { font-size: 11px; padding: 8px; }
            #similarPlayersGrid img { width: 50px; height: 50px; }
            
            /* Footer */
            .site-footer { padding: 20px 15px; font-size: 12px; }
            .footer-links { 
                display: flex; 
                flex-direction: column; 
                gap: 8px; 
            }
            .footer-links a { margin: 0; display: block; }
            
            /* Terms modal on mobile */
            #termsModal { padding: 15px; }
            #termsModal > div { 
                padding: 20px; 
                font-size: 13px;
                max-height: 80vh;
                overflow-y: auto;
            }
            #termsModal h2 { font-size: 18px; }
            #termsModal h3 { font-size: 15px; margin-top: 15px; }
            #termsModal ul { margin-left: 20px; font-size: 12px; }
            #termsModal button { font-size: 14px; padding: 10px 20px; }
        }
        
        /* Small phones */
        @media (max-width: 480px) {
            .site-title { font-size: 24px; }
            h1 { font-size: 18px; }
            table { font-size: 9px; }
            th, td { padding: 6px 3px; }
            
            /* Even narrower player column on small phones */
            .player-name {
                max-width: 100px !important;
                min-width: 100px !important;
            }
            
            .viz-tab { font-size: 10px; padding: 6px 8px; }
            
            /* Taller charts on small phones too */
            canvas {
                min-height: 320px !important;
            }
            #playerProfileContent canvas {
                height: 320px !important;
            }
            
            #similarPlayersGrid { grid-template-columns: 1fr !important; }
            #playerHeader > div { 
                grid-template-columns: 1fr;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <!-- Site Header with Logo -->
    <div class="site-header">
        <div class="logo-container">
            <div class="logo-icon">
                <div class="arc arc-1"></div>
                <div class="arc arc-2"></div>
                <div class="arc arc-3"></div>
                <div class="arc arc-4"></div>
            </div>
        </div>
        <h1 class="site-title">3point.app</h1>
        <p class="site-tagline">Advanced 3-Point Shooting Analytics</p>
    </div>

    <div class="container">
        <h1>NBA 3P% Over Expected (3P%OE) Leaderboard</h1>
        <p class="subtitle">Multi-Season Data (2013-14 to Present) | Qualified players: 82 3PA (season) / 250 3PM (career)</p>

        <!-- Main Navigation Tabs -->
        <div class="main-nav">
            <button class="main-tab active" onclick="showMainView('table')">Table View</button>
            <button class="main-tab" onclick="showMainView('visualizations')">Visualizations</button>
            <button class="main-tab" onclick="showMainView('player-profile')">Player Profile</button>
            <button class="main-tab" onclick="showMainView('about')">About</button>
        </div>

        <!-- Table View -->
        <div id="table-view" class="main-view active">
            <!-- Legend -->
            <div class="legend" style="margin-top: 30px;">
                <div class="legend-item"><div class="legend-box very-tight"></div><span>Very Tight (0-2 ft)</span></div>
                <div class="legend-item"><div class="legend-box tight"></div><span>Tight (2-4 ft)</span></div>
                <div class="legend-item"><div class="legend-box open"></div><span>Open (4-6 ft)</span></div>
                <div class="legend-item"><div class="legend-box wide-open"></div><span>Wide Open (6+ ft)</span></div>
            </div>

        <div class="controls">
            <div>
                <label for="seasonSelect">Season:</label>
                <select id="seasonSelect" class="season-selector"></select>
            </div>
            <div>
                <label for="search">Search Player:</label>
                <input type="text" id="search" placeholder="Enter player name...">
            </div>
            <div>
                <label for="minAttempts">Min Total 3PA:</label>
                <input type="number" id="minAttempts" value="0" min="0" style="width: 80px;">
            </div>
        </div>

        <div class="table-wrapper">
            <table id="statsTable">
                <thead>
                    <tr>
                        <th class="sortable" data-column="rank" rowspan="2" title="Rank by 3PES">#</th>
                        <th class="sortable" data-column="player" rowspan="2" title="Player Name">Player</th>
                        <th class="sortable stat-value" data-column="3pes" rowspan="2" style="background-color: #e1f5fe; font-weight: bold;" title="3-Point Efficiency Score - Ranks how good a 3-point shooter was for that season. Combines accuracy, shot difficulty, and volume. Legendary: 30+, Elite: 20-30, Good: 10-20">3PES</th>
                        <th class="sortable stat-value" data-column="3p_pct_oe" rowspan="2" style="background-color: #fff9c4; font-weight: bold;" title="3-Point % Over Expected - How much better/worse a player shoots vs league average, weighted by their shot distribution. Accounts for shot difficulty">3P%OE</th>
                        <th class="sortable stat-value" data-column="3paa" rowspan="2" style="background-color: #f3e5f5; font-weight: bold;" title="3-Point Above Average - Total extra points this player scored (vs league average shooter) from 3-pointers. Calculated as 3P%OE × 3PM. Higher = more total value added">3PAA</th>
                        <th class="sortable stat-value" data-column="total_3pm" rowspan="2" title="Total 3-pointers made">Total<br>3PM</th>
                        <th class="sortable stat-value" data-column="total_3pa" rowspan="2" title="Total 3-point attempts - Minimum 82 for single season, 250 3PM for career">Total<br>3PA</th>
                        <th class="group-header very-tight" colspan="4" title="Shots with defender 0-2 feet away - Most difficult shots">Very Tight (0-2 ft)</th>
                        <th class="group-header tight" colspan="4" title="Shots with defender 2-4 feet away - Contested shots">Tight (2-4 ft)</th>
                        <th class="group-header open" colspan="4" title="Shots with defender 4-6 feet away - Open shots">Open (4-6 ft)</th>
                        <th class="group-header wide-open" colspan="4" title="Shots with defender 6+ feet away - Wide open shots">Wide Open (6+ ft)</th>
                    </tr>
                    <tr>
                        <th class="sortable stat-value very-tight" data-column="very_tight_3pm" title="3-pointers made with very tight defense (0-2ft)">3PM</th>
                        <th class="sortable stat-value very-tight" data-column="very_tight_3pa" title="3-point attempts with very tight defense (0-2ft)">3PA</th>
                        <th class="sortable stat-value very-tight" data-column="very_tight_3p_pct" title="3-point % with very tight defense">3P%</th>
                        <th class="sortable stat-value very-tight" data-column="very_tight_freq" title="% of player's total 3PA at this defender distance">Freq%</th>
                        <th class="sortable stat-value tight" data-column="tight_3pm" title="3-pointers made with tight defense (2-4ft)">3PM</th>
                        <th class="sortable stat-value tight" data-column="tight_3pa" title="3-point attempts with tight defense (2-4ft)">3PA</th>
                        <th class="sortable stat-value tight" data-column="tight_3p_pct" title="3-point % with tight defense">3P%</th>
                        <th class="sortable stat-value tight" data-column="tight_freq" title="% of player's total 3PA at this defender distance">Freq%</th>
                        <th class="sortable stat-value open" data-column="open_3pm" title="3-pointers made when open (4-6ft)">3PM</th>
                        <th class="sortable stat-value open" data-column="open_3pa" title="3-point attempts when open (4-6ft)">3PA</th>
                        <th class="sortable stat-value open" data-column="open_3p_pct" title="3-point % when open">3P%</th>
                        <th class="sortable stat-value open" data-column="open_freq" title="% of player's total 3PA at this defender distance">Freq%</th>
                        <th class="sortable stat-value wide-open" data-column="wide_open_3pm" title="3-pointers made when wide open (6+ft)">3PM</th>
                        <th class="sortable stat-value wide-open" data-column="wide_open_3pa" title="3-point attempts when wide open (6+ft)">3PA</th>
                        <th class="sortable stat-value wide-open" data-column="wide_open_3p_pct" title="3-point % when wide open">3P%</th>
                        <th class="sortable stat-value wide-open" data-column="wide_open_freq" title="% of player's total 3PA at this defender distance">Freq%</th>
                    </tr>
                </thead>
                <tbody id="tableBody"></tbody>
            </table>
        </div>

        <div class="footer">
            Click column headers to sort | 3P%OE = 3-Point % Over Expected | 3PAA = 3-Point Above Average (total impact) | 3PES = 3-Point Efficiency Score (volume-adjusted)
        </div>
        </div>

        <!-- Visualizations View -->
        <div id="visualizations-view" class="main-view">
            <div class="viz-container">
                <h2>Visualizations</h2>
                
                <!-- Visualization Controls -->
                <div class="controls" style="margin-bottom: 20px;">
                    <div>
                        <label for="vizSeasonSelect">Season:</label>
                        <select id="vizSeasonSelect" class="season-selector"></select>
                    </div>
                    <div id="playerFilterContainer" style="display: none;">
                        <label for="playerFilter">Compare Players:</label>
                        <input type="text" id="playerFilter" placeholder="Start typing player names...">
                        <div id="playerSuggestions" style="position: absolute; background: white; border: 1px solid #ccc; max-height: 200px; overflow-y: auto; display: none; z-index: 1000;"></div>
                    </div>
                    <div id="selectedPlayers" style="display: flex; gap: 10px; flex-wrap: wrap;"></div>
                </div>
                
                <div class="viz-tabs">
                    <button class="viz-tab active" onclick="showViz('scatter')">3P%OE vs Volume</button>
                    <button class="viz-tab" onclick="showViz('metrics')">3PAA vs 3PES</button>
                    <button class="viz-tab" onclick="showViz('efficiency')">Player Comparison - Efficiency by Distance</button>
                    <button class="viz-tab" onclick="showViz('cumulative')">Cumulative Stats</button>
                    <button class="viz-tab" onclick="showViz('best3pes')">Best 3PES Seasons</button>
                </div>
                <div id="scatter-viz" class="viz-panel active">
                    <canvas id="scatterChart"></canvas>
                    <div class="viz-info">
                        <strong>What to look for:</strong> Top-right = Elite shooters (high volume + high efficiency). Top-left = Efficient low-volume shooters. Red trendline shows average relationship. Players above the line overperform given their volume.
                    </div>
                </div>
                <div id="metrics-viz" class="viz-panel">
                    <canvas id="metricsChart"></canvas>
                    <div class="viz-info">
                        <strong>What to look for:</strong> 3PAA (X) rewards total value. 3PES (Y) penalizes volume. Top-right = Elite in both. Above trendline = exceptional efficiency despite volume.
                    </div>
                </div>
                <div id="efficiency-viz" class="viz-panel">
                    <canvas id="efficiencyChart"></canvas>
                    <div class="viz-info">
                        <strong>What to look for:</strong> Select up to 5 players to compare. Larger shapes = better at that distance. See who excels when guarded vs. wide open. Compare to league average.
                    </div>
                </div>
                <div id="best3pes-viz" class="viz-panel">
                    <div id="best3pesTable" style="max-height: 600px; overflow-y: auto;"></div>
                    <div class="viz-info">
                        <strong>What to look for:</strong> Greatest single-season 3PT performances (min 82 attempts). Bar shows 3PES relative to #1. Click players to view full profile.
                    </div>
                </div>
                <div id="cumulative-viz" class="viz-panel">
                    <canvas id="cumulativeChart"></canvas>
                    <div class="viz-info">
                        <strong>What to look for:</strong> Steeper slopes = more value per season. Young players with steep slopes catching veterans. Flat lines = injuries/decline. Hover to identify.
                    </div>
                </div>
            </div>
        </div>

        <!-- Player Profile View -->
        <div id="player-profile-view" class="main-view">
            <div style="margin: 20px 0;">
                <label for="playerProfileSelect" style="font-size: 16px; font-weight: bold; margin-right: 10px;">Search Player:</label>
                <div style="position: relative;">
                    <input type="text" id="playerProfileSelect" placeholder="Start typing player name..." style="padding: 10px; font-size: 15px; min-width: 300px; border: 2px solid #2196F3;">
                    <div id="playerProfileSuggestions" style="position: absolute; background: white; border: 2px solid #2196F3; border-top: none; max-height: 300px; overflow-y: auto; display: none; z-index: 1000; width: 100%;"></div>
                </div>
            </div>
            
            <div id="playerProfileContent" style="display: none;">
                <!-- Player Header -->
                <div id="playerHeader" style="display: flex; align-items: center; gap: 20px; margin: 30px 0; padding: 20px; background: #f9f9f9; border-radius: 8px;">
                    <div id="playerPhotoLarge"></div>
                    <div id="playerStats"></div>
                </div>
                
                <!-- Player Charts -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <canvas id="playerDistributionChart"></canvas>
                    </div>
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <canvas id="playerEfficiencyChart"></canvas>
                    </div>
                </div>
                
                <!-- Similar Players Section -->
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px;">
                    <h3 style="margin-bottom: 15px;">Similar Players (by Shot Profile)</h3>
                    <div id="similarPlayersGrid" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px;"></div>
                </div>
                
                <!-- Season-by-Season Table -->
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h3>Season-by-Season Statistics</h3>
                    <div id="playerSeasonTable" style="overflow-x: auto;"></div>
                </div>
            </div>
            
            <div id="playerProfilePlaceholder" style="text-align: center; padding: 60px; color: #999; font-size: 18px;">
                Select a player to view their profile
            </div>
        </div>
        
        <!-- About & Glossary View -->
        <div id="about-view" class="main-view">
            <div style="max-width: 900px; margin: 0 auto; padding: 20px;">
                <h1 style="font-size: 32px; margin-bottom: 30px; color: #1a365d;">About & Glossary</h1>
                
                <!-- What is 3point.app -->
                <section style="margin-bottom: 40px;">
                    <h2 style="font-size: 24px; margin-bottom: 15px; color: #2196F3;">What is 3point.app?</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        3point.app provides advanced NBA 3-point shooting analytics with detailed defender distance breakdowns. The platform seeks to quantify what the eye test tells us: some shooters are more efficient than raw percentages suggest because they consistently make difficult shots. Our proprietary metrics (3PES, 3P%OE, and 3PAA) account for shot difficulty and volume to identify the league's most efficient three-point shooters. The platform tracks ''' + str(num_seasons) + ''' seasons of data (2013-14 through present) and offers comprehensive public analysis of how players perform under different defensive pressures.
                    </p>
                </section>
                
                <!-- Metric Glossary -->
                <section style="margin-bottom: 40px;">
                    <h2 style="font-size: 24px; margin-bottom: 15px; color: #2196F3;">Metric Glossary</h2>
                    
                    <div style="background: #e1f5fe; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #2196F3;">
                        <h3 style="font-size: 18px; margin-bottom: 10px; color: #1a365d;">3PES (3-Point Efficiency Score)</h3>
                        <p style="font-size: 15px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                            A volume-adjusted metric that ranks overall 3-point shooting performance by combining accuracy, shot difficulty, and total output. Higher scores indicate more efficient, high-volume shooters. 3PES can be used to determine the best three-point shooter for a given season or across an entire career.
                        </p>
                        <ul style="font-size: 15px; line-height: 1.6; color: #333; list-style-position: inside;">
                            <li><strong>Legendary:</strong> 30+</li>
                            <li><strong>Elite:</strong> 20-30</li>
                            <li><strong>Good:</strong> 10-20</li>
                        </ul>
                    </div>
                    
                    <div style="background: #fff9c4; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #FFC107;">
                        <h3 style="font-size: 18px; margin-bottom: 10px; color: #1a365d;">3P%OE (3-Point Percentage Over Expected)</h3>
                        <p style="font-size: 15px; line-height: 1.6; color: #333;">
                            Measures how much better or worse a player shoots compared to league average, weighted by defender distance distribution. A player shooting +5.0% performs 5 percentage points above expectation given their shot profile. This metric adjusts for shot difficulty: shooting 40% on contested shots is more valuable than 40% on wide-open looks.
                        </p>
                    </div>
                    
                    <div style="background: #f3e5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #9C27B0;">
                        <h3 style="font-size: 18px; margin-bottom: 10px; color: #1a365d;">3PAA (3-Point Above Average)</h3>
                        <p style="font-size: 15px; line-height: 1.6; color: #333;">
                            Quantifies total value added from three-point shooting. Calculated as 3P%OE multiplied by three-pointers made, representing the cumulative extra points a player generates compared to an average shooter taking the same shots. A 3PAA of +150 means the player scored 150 more points from three than expected.
                        </p>
                    </div>
                    
                    <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #666;">
                        <h3 style="font-size: 18px; margin-bottom: 10px; color: #1a365d;">Defender Distance Categories</h3>
                        <ul style="font-size: 15px; line-height: 1.8; color: #333; list-style-position: inside;">
                            <li><strong>Very Tight (0-2 feet):</strong> Closest defender within 2 feet at release</li>
                            <li><strong>Tight (2-4 feet):</strong> Defender 2-4 feet away</li>
                            <li><strong>Open (4-6 feet):</strong> Defender 4-6 feet away</li>
                            <li><strong>Wide Open (6+ feet):</strong> Defender more than 6 feet away</li>
                        </ul>
                    </div>
                </section>
                
                <!-- Data & Methodology -->
                <section style="margin-bottom: 40px;">
                    <h2 style="font-size: 24px; margin-bottom: 15px; color: #2196F3;">Data & Methodology</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Data Source:</strong> NBA.com
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Coverage:</strong> ''' + first_season + ''' season through ''' + latest_season + ''' season
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Qualification Standards:</strong>
                    </p>
                    <ul style="font-size: 16px; line-height: 1.6; color: #333; margin-left: 20px; margin-bottom: 10px;">
                        <li>Single season: Minimum 82 three-point attempts (pro-rated at 1 per team game for the season in progress''' + (f' — currently {latest_qual} for {latest_season}' if latest_qual < 82 else '') + ''')</li>
                        <li>Career: Minimum 250 three-point makes</li>
                    </ul>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Calculation Methodology:</strong>
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        League average three-point percentages are calculated separately for each defender distance category and season.
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-top: 10px;">
                        <strong>Update Frequency:</strong> Data is refreshed weekly during the NBA season.
                    </p>
                </section>
                
                <!-- How to Use -->
                <section style="margin-bottom: 40px;">
                    <h2 style="font-size: 24px; margin-bottom: 15px; color: #2196F3;">How to Use the Site</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Table View:</strong> Sort by any metric to identify league leaders. Use the search bar to find specific players. Swipe horizontally on mobile to view all columns.
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        <strong>Player Profile:</strong> Select any qualified player to view career statistics, season-by-season breakdowns, shooting charts by defender distance, and algorithmically-generated similar players based on shooting profile.
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        <strong>Visualizations (Desktop Only):</strong> Interactive scatter plots and comparative charts.
                    </p>
                </section>
                
                <!-- Contact -->
                <section style="margin-bottom: 40px;">
                    <h2 style="font-size: 24px; margin-bottom: 15px; color: #2196F3;">Contact</h2>
                    <p style="font-size: 16px; line-height: 1.6; color: #333; margin-bottom: 10px;">
                        For inquiries, advertising, or data licensing: <a href="mailto:deeprangedata@gmail.com" style="color: #2196F3;">deeprangedata@gmail.com</a>
                    </p>
                    <p style="font-size: 16px; line-height: 1.6; color: #333;">
                        3PES, 3P%OE, and 3PAA are proprietary metrics. For commercial use or redistribution, please contact us. See our <a href="#" onclick="document.getElementById('termsModal').style.display='flex'" style="color: #2196F3;">Terms of Service</a> for full usage guidelines.
                    </p>
                </section>
                
                <!-- Last Updated -->
                <section style="margin-top: 50px; padding-top: 30px; border-top: 2px solid #ddd;">
                    <p style="font-size: 14px; color: #666; text-align: center;" id="lastUpdatedDate">
                        Last Updated: Loading...
                    </p>
                </section>
            </div>
        </div>
    </div>

    <script>
        const allSeasonData = ''' + json.dumps(all_data) + ''';
        const LAST_UPDATED = "''' + last_updated_iso + '''";
        const LATEST_SEASON = "''' + latest_season + '''";
        const LATEST_SEASON_QUAL = ''' + str(latest_qual) + ''';
        // 82 3PA for completed seasons; pro-rated for the season in progress
        function seasonQualMin(season) {
            return season === LATEST_SEASON ? LATEST_SEASON_QUAL : 82;
        }
        
        let currentSeason = 'Career';
        let currentVizSeason = 'Career';
        let selectedPlayers = [];
        let currentData = [];
        let sortColumn = null;
        let sortDirection = 'asc';
        let playerProfileCharts = {};

        function safeValue(obj, key, defaultVal = 0) {
            return (obj && obj[key] !== undefined && obj[key] !== null) ? obj[key] : defaultVal;
        }
        
        function calculateTrendline(data) {
            // Calculate linear regression
            const n = data.length;
            let sumX = 0, sumY = 0, sumXY = 0, sumXX = 0;
            
            data.forEach(point => {
                sumX += point.x;
                sumY += point.y;
                sumXY += point.x * point.y;
                sumXX += point.x * point.x;
            });
            
            const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
            const intercept = (sumY - slope * sumX) / n;
            
            // Generate trendline points
            const minX = Math.min(...data.map(p => p.x));
            const maxX = Math.max(...data.map(p => p.x));
            
            return [
                { x: minX, y: slope * minX + intercept },
                { x: maxX, y: slope * maxX + intercept }
            ];
        }

        function populateSeasonSelector() {
            const selector = document.getElementById('seasonSelect');
            const vizSelector = document.getElementById('vizSeasonSelect');
            const seasons = Object.keys(allSeasonData);
            
            // Put Career first, then reverse chronological order
            const sortedSeasons = seasons.sort((a, b) => {
                if (a === 'Career') return -1;
                if (b === 'Career') return 1;
                return b.localeCompare(a);
            });
            
            sortedSeasons.forEach(season => {
                const option = document.createElement('option');
                option.value = season;
                option.textContent = season;
                selector.appendChild(option);
                
                const vizOption = option.cloneNode(true);
                vizSelector.appendChild(vizOption);
            });
            
            selector.value = 'Career';
            vizSelector.value = 'Career';
        }
        
        function populatePlayerProfileDropdown() {
            const input = document.getElementById('playerProfileSelect');
            const suggestionsDiv = document.getElementById('playerProfileSuggestions');
            const careerData = allSeasonData['Career'] || [];
            
            // Get qualified players and sort alphabetically
            const qualifiedPlayers = careerData
                .filter(p => safeValue(p, 'total_3pm', 0) >= 250)
                .sort((a, b) => safeValue(a, 'player', '').localeCompare(safeValue(b, 'player', '')));
            
            input.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase();
                
                if (searchTerm.length < 2) {
                    suggestionsDiv.style.display = 'none';
                    return;
                }
                
                const matches = qualifiedPlayers.filter(p => 
                    safeValue(p, 'player', '').toLowerCase().includes(searchTerm)
                ).slice(0, 15);
                
                if (matches.length > 0) {
                    suggestionsDiv.innerHTML = matches.map(p => {
                        const playerName = safeValue(p, 'player', '');
                        return `<div style="padding: 10px; cursor: pointer; border-bottom: 1px solid #eee;" 
                                     onmouseover="this.style.backgroundColor='#f0f0f0'" 
                                     onmouseout="this.style.backgroundColor='white'"
                                     onclick="selectPlayerProfile('${playerName.replace(/'/g, "\\'")}')">${playerName}</div>`;
                    }).join('');
                    suggestionsDiv.style.display = 'block';
                } else {
                    suggestionsDiv.innerHTML = '<div style="padding: 10px; color: #999;">No players found</div>';
                    suggestionsDiv.style.display = 'block';
                }
            });
            
            // Close suggestions when clicking outside
            document.addEventListener('click', function(e) {
                if (e.target.id !== 'playerProfileSelect' && e.target.id !== 'playerProfileSuggestions') {
                    suggestionsDiv.style.display = 'none';
                }
            });
        }
        
        function selectPlayerProfile(playerName) {
            document.getElementById('playerProfileSelect').value = playerName;
            document.getElementById('playerProfileSuggestions').style.display = 'none';
            loadPlayerProfile(playerName);
        }
        
        function loadPlayerProfile(playerName) {
            document.getElementById('playerProfilePlaceholder').style.display = 'none';
            document.getElementById('playerProfileContent').style.display = 'block';
            
            // Get career data
            const careerData = allSeasonData['Career'] || [];
            const careerPlayer = careerData.find(p => safeValue(p, 'player', '') === playerName);
            
            // Get all seasons for this player
            const playerSeasons = [];
            Object.keys(allSeasonData).forEach(season => {
                if (season !== 'Career') {
                    const seasonData = allSeasonData[season] || [];
                    const playerSeason = seasonData.find(p => safeValue(p, 'player', '') === playerName);
                    if (playerSeason && safeValue(playerSeason, 'total_3pa', 0) >= seasonQualMin(season)) {
                        playerSeasons.push({...playerSeason, season: season});
                    }
                }
            });
            
            // Sort seasons chronologically
            playerSeasons.sort((a, b) => a.season.localeCompare(b.season));
            
            // Display player header
            displayPlayerHeader(careerPlayer, playerSeasons.length);
            
            // Display charts
            displayPlayerCharts(careerPlayer);
            
            // Display similar players
            displaySimilarPlayers(careerPlayer);
            
            // Display season table
            displayPlayerSeasonTable(playerSeasons);
        }
        
        function displaySimilarPlayers(player) {
            const playerName = safeValue(player, 'player', '');
            const careerData = allSeasonData['Career'] || [];
            const qualifiedPlayers = careerData.filter(p => 
                safeValue(p, 'total_3pm', 0) >= 250 && 
                safeValue(p, 'player', '') !== playerName
            );
            
            // Calculate similarity score based on shot distribution
            const playerDist = [
                safeValue(player, 'very_tight_freq', 0),
                safeValue(player, 'tight_freq', 0),
                safeValue(player, 'open_freq', 0),
                safeValue(player, 'wide_open_freq', 0)
            ];
            
            const similarities = qualifiedPlayers.map(p => {
                const pDist = [
                    safeValue(p, 'very_tight_freq', 0),
                    safeValue(p, 'tight_freq', 0),
                    safeValue(p, 'open_freq', 0),
                    safeValue(p, 'wide_open_freq', 0)
                ];
                
                // Calculate Euclidean distance
                let distanceSum = 0;
                for (let i = 0; i < 4; i++) {
                    distanceSum += Math.pow(playerDist[i] - pDist[i], 2);
                }
                const distance = Math.sqrt(distanceSum);
                
                return {
                    player: p,
                    similarity: 100 - distance // Higher is more similar
                };
            });
            
            // Sort by similarity and take top 5
            const top5Similar = similarities
                .sort((a, b) => b.similarity - a.similarity)
                .slice(0, 5);
            
            const container = document.getElementById('similarPlayersGrid');
            container.innerHTML = top5Similar.map(s => {
                const p = s.player;
                const playerId = safeValue(p, 'player_id', null);
                const pName = safeValue(p, 'player', 'Unknown');
                
                let photoHTML = '';
                if (playerId) {
                    photoHTML = `<img src="https://cdn.nba.com/headshots/nba/latest/260x190/${playerId}.png" 
                                     onError="this.style.display='none'"
                                     style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #2196F3; margin-bottom: 10px;">`;
                } else {
                    photoHTML = '<div style="width: 80px; height: 80px; border-radius: 50%; background-color: #e0e0e0; margin-bottom: 10px;"></div>';
                }
                
                return `
                    <div style="text-align: center; cursor: pointer; padding: 10px; border-radius: 8px; transition: background 0.2s;" 
                         onmouseover="this.style.backgroundColor='#f5f5f5'" 
                         onmouseout="this.style.backgroundColor='white'"
                         onclick="selectPlayerProfile('${pName.replace(/'/g, "\\'")}')">
                        ${photoHTML}
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 5px;">${pName}</div>
                        <div style="font-size: 12px; color: #666;">3P%OE: ${safeValue(p, '3p_pct_oe', 0) >= 0 ? '+' : ''}${safeValue(p, '3p_pct_oe', 0).toFixed(2)}%</div>
                        <div style="font-size: 11px; color: #999; margin-top: 5px;">Similarity: ${s.similarity.toFixed(0)}%</div>
                    </div>
                `;
            }).join('');
        }
        
        function displayPlayerHeader(player, numSeasons) {
            const playerId = safeValue(player, 'player_id', null);
            const playerName = safeValue(player, 'player', 'Unknown');
            
            let photoHTML = '';
            if (playerId) {
                photoHTML = `<img src="https://cdn.nba.com/headshots/nba/latest/260x190/${playerId}.png" 
                                 style="width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 4px solid #2196F3;"
                                 onerror="this.style.display='none';">`;
            }
            
            document.getElementById('playerPhotoLarge').innerHTML = photoHTML;
            
            const statsHTML = `
                <div>
                    <h2 style="margin: 0 0 10px 0;">${playerName}</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; font-size: 14px;">
                        <div><strong>Seasons:</strong> ${numSeasons}</div>
                        <div><strong>Career 3PM:</strong> ${safeValue(player, 'total_3pm', 0)}</div>
                        <div><strong>Career 3PA:</strong> ${safeValue(player, 'total_3pa', 0)}</div>
                        <div style="font-size: 16px; color: #2196F3;"><strong>3P%OE:</strong> ${safeValue(player, '3p_pct_oe', 0) >= 0 ? '+' : ''}${safeValue(player, '3p_pct_oe', 0).toFixed(2)}%</div>
                        <div style="font-size: 16px; color: #9C27B0;"><strong>3PAA:</strong> ${safeValue(player, '3paa', 0).toFixed(2)}</div>
                        <div style="font-size: 16px; color: #00BCD4;"><strong>3PES:</strong> ${safeValue(player, '3pes', 0).toFixed(2)}</div>
                    </div>
                </div>
            `;
            
            document.getElementById('playerStats').innerHTML = statsHTML;
        }
        
        function displayPlayerCharts(player) {
            // Clear existing charts
            if (playerProfileCharts.distribution) playerProfileCharts.distribution.destroy();
            if (playerProfileCharts.efficiency) playerProfileCharts.efficiency.destroy();
            
            // Shot Distribution Chart
            const distCtx = document.getElementById('playerDistributionChart').getContext('2d');
            
            const totalAttempts = safeValue(player, 'very_tight_3pa', 0) + 
                                 safeValue(player, 'tight_3pa', 0) + 
                                 safeValue(player, 'open_3pa', 0) + 
                                 safeValue(player, 'wide_open_3pa', 0);
            
            playerProfileCharts.distribution = new Chart(distCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Very Tight (0-2 ft)', 'Tight (2-4 ft)', 'Open (4-6 ft)', 'Wide Open (6+ ft)'],
                    datasets: [{
                        data: [
                            safeValue(player, 'very_tight_3pa', 0),
                            safeValue(player, 'tight_3pa', 0),
                            safeValue(player, 'open_3pa', 0),
                            safeValue(player, 'wide_open_3pa', 0)
                        ],
                        backgroundColor: [
                            'rgba(244, 67, 54, 0.7)',
                            'rgba(255, 152, 0, 0.7)',
                            'rgba(76, 175, 80, 0.7)',
                            'rgba(33, 150, 243, 0.7)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Career Shot Distribution',
                            font: { size: 16 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const value = context.parsed;
                                    const percentage = ((value / totalAttempts) * 100).toFixed(1);
                                    return `${context.label}: ${value} attempts (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
            
            // Efficiency Radar Chart
            const effCtx = document.getElementById('playerEfficiencyChart').getContext('2d');
            
            const playerData = {
                vt: { pct: safeValue(player, 'very_tight_3p_pct', 0), att: safeValue(player, 'very_tight_3pa', 0), made: safeValue(player, 'very_tight_3pm', 0) },
                t: { pct: safeValue(player, 'tight_3p_pct', 0), att: safeValue(player, 'tight_3pa', 0), made: safeValue(player, 'tight_3pm', 0) },
                o: { pct: safeValue(player, 'open_3p_pct', 0), att: safeValue(player, 'open_3pa', 0), made: safeValue(player, 'open_3pm', 0) },
                wo: { pct: safeValue(player, 'wide_open_3p_pct', 0), att: safeValue(player, 'wide_open_3pa', 0), made: safeValue(player, 'wide_open_3pm', 0) }
            };
            
            // Calculate league averages
            const careerData = allSeasonData['Career'] || [];
            const qualifiedPlayers = careerData.filter(p => safeValue(p, 'total_3pm', 0) >= 250);
            
            let leagueAvg = { vt: 0, t: 0, o: 0, wo: 0, count: 0 };
            qualifiedPlayers.forEach(p => {
                leagueAvg.vt += safeValue(p, 'very_tight_3p_pct', 0);
                leagueAvg.t += safeValue(p, 'tight_3p_pct', 0);
                leagueAvg.o += safeValue(p, 'open_3p_pct', 0);
                leagueAvg.wo += safeValue(p, 'wide_open_3p_pct', 0);
                leagueAvg.count++;
            });
            
            const avgData = [
                leagueAvg.vt / leagueAvg.count,
                leagueAvg.t / leagueAvg.count,
                leagueAvg.o / leagueAvg.count,
                leagueAvg.wo / leagueAvg.count
            ];
            
            const maxPct = Math.max(playerData.vt.pct, playerData.t.pct, playerData.o.pct, playerData.wo.pct, ...avgData);
            const radarMax = Math.min(100, Math.ceil((maxPct + 10) / 10) * 10); // Round up to nearest 10, cap at 100
            
            playerProfileCharts.efficiency = new Chart(effCtx, {
                type: 'radar',
                data: {
                    labels: ['Very Tight', 'Tight', 'Open', 'Wide Open'],
                    datasets: [{
                        label: safeValue(player, 'player', 'Player'),
                        data: [playerData.vt.pct, playerData.t.pct, playerData.o.pct, playerData.wo.pct],
                        attempts: [playerData.vt.att, playerData.t.att, playerData.o.att, playerData.wo.att],
                        makes: [playerData.vt.made, playerData.t.made, playerData.o.made, playerData.wo.made],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.2)',
                        borderWidth: 3
                    }, {
                        label: 'League Average',
                        data: avgData,
                        borderColor: '#999',
                        backgroundColor: 'rgba(153, 153, 153, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Career 3P% by Defender Distance vs League Average',
                            font: { size: 16 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    if (context.datasetIndex === 0) {
                                        const idx = context.dataIndex;
                                        const pct = context.parsed.r;
                                        const att = context.dataset.attempts[idx];
                                        const made = context.dataset.makes[idx];
                                        return [
                                            `${context.dataset.label}: ${pct.toFixed(1)}%`,
                                            `${made}/${att} 3PT`
                                        ];
                                    } else {
                                        return `${context.dataset.label}: ${context.parsed.r.toFixed(1)}%`;
                                    }
                                }
                            }
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: radarMax,
                            ticks: { stepSize: 10 }
                        }
                    }
                }
            });
        }
        
        function displayPlayerSeasonTable(seasons) {
            // Get career data
            const careerData = allSeasonData['Career'] || [];
            const careerPlayer = careerData.find(p => safeValue(p, 'player', '') === seasons[0]?.player);
            
            // Calculate rankings for each season
            const seasonsWithRanks = seasons.map(s => {
                const seasonData = allSeasonData[s.season] || [];
                const qualifiedPlayers = seasonData.filter(p => safeValue(p, 'total_3pa', 0) >= seasonQualMin(s.season));
                const sorted = qualifiedPlayers.sort((a, b) => safeValue(b, '3pes', 0) - safeValue(a, '3pes', 0));
                const rank = sorted.findIndex(p => safeValue(p, 'player', '') === s.player) + 1;
                return {...s, rank: rank > 0 ? rank : null};
            });
            
            // Calculate career rank
            let careerRank = null;
            if (careerPlayer) {
                const qualifiedCareer = careerData.filter(p => safeValue(p, 'total_3pm', 0) >= 250);
                const sortedCareer = qualifiedCareer.sort((a, b) => safeValue(b, '3pes', 0) - safeValue(a, '3pes', 0));
                careerRank = sortedCareer.findIndex(p => safeValue(p, 'player', '') === safeValue(careerPlayer, 'player', '')) + 1;
            }
            
            let html = `
                <table class="best3pes-table">
                    <thead>
                        <tr>
                            <th title="Season or Career totals">Season</th>
                            <th class="stat-col" title="3-Point Efficiency Score - Ranks how good a 3-point shooter was for that season. Combines accuracy, shot difficulty, and volume. Legendary: 30+, Elite: 20-30, Good: 10-20">3PES</th>
                            <th class="stat-col" title="3-Point % Over Expected - Weighted by shot difficulty">3P%OE</th>
                            <th class="stat-col" title="3-Point Above Average - Total extra points scored (vs league average) from 3-pointers">3PAA</th>
                            <th class="stat-col" title="3-pointers made">3PM</th>
                            <th class="stat-col" title="3-point attempts">3PA</th>
                            <th class="stat-col" title="3P% when defender 0-2 feet away">VT%</th>
                            <th class="stat-col" title="3P% when defender 2-4 feet away">T%</th>
                            <th class="stat-col" title="3P% when defender 4-6 feet away">O%</th>
                            <th class="stat-col" title="3P% when defender 6+ feet away">WO%</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            seasonsWithRanks.forEach(s => {
                const rankText = s.rank ? `<div style="font-size: 11px; color: #999; font-style: italic; margin-top: 2px;">#${s.rank}</div>` : '';
                html += `
                    <tr>
                        <td style="font-weight: bold;">${s.season}</td>
                        <td class="stat-col">
                            <div>${safeValue(s, '3pes', 0).toFixed(2)}</div>
                            ${rankText}
                        </td>
                        <td class="stat-col">${safeValue(s, '3p_pct_oe', 0) >= 0 ? '+' : ''}${safeValue(s, '3p_pct_oe', 0).toFixed(2)}%</td>
                        <td class="stat-col">${safeValue(s, '3paa', 0).toFixed(2)}</td>
                        <td class="stat-col">${safeValue(s, 'total_3pm', 0)}</td>
                        <td class="stat-col">${safeValue(s, 'total_3pa', 0)}</td>
                        <td class="stat-col">${safeValue(s, 'very_tight_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(s, 'tight_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(s, 'open_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(s, 'wide_open_3p_pct', 0).toFixed(1)}%</td>
                    </tr>
                `;
            });
            
            // Add career row
            if (careerPlayer) {
                const careerRankText = careerRank ? `<div style="font-size: 11px; color: #999; font-style: italic; margin-top: 2px;">#${careerRank}</div>` : '';
                html += `
                    <tr style="border-top: 3px solid #2196F3; background-color: #f0f8ff; font-weight: bold;">
                        <td>Career</td>
                        <td class="stat-col">
                            <div>${safeValue(careerPlayer, '3pes', 0).toFixed(2)}</div>
                            ${careerRankText}
                        </td>
                        <td class="stat-col">${safeValue(careerPlayer, '3p_pct_oe', 0) >= 0 ? '+' : ''}${safeValue(careerPlayer, '3p_pct_oe', 0).toFixed(2)}%</td>
                        <td class="stat-col">${safeValue(careerPlayer, '3paa', 0).toFixed(2)}</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'total_3pm', 0)}</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'total_3pa', 0)}</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'very_tight_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'tight_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'open_3p_pct', 0).toFixed(1)}%</td>
                        <td class="stat-col">${safeValue(careerPlayer, 'wide_open_3p_pct', 0).toFixed(1)}%</td>
                    </tr>
                `;
            }
            
            html += `
                    </tbody>
                </table>
            `;
            
            document.getElementById('playerSeasonTable').innerHTML = html;
        }

        function renderTable(data) {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            if (!data || data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="25" style="text-align: center; padding: 20px;">No data to display</td></tr>';
                return;
            }

            data.forEach((player, index) => {
                if (!player) return;
                
                const row = document.createElement('tr');
                const playerName = safeValue(player, 'player', 'Unknown');
                const playerId = safeValue(player, 'player_id', null);
                const oe = safeValue(player, '3p_pct_oe', 0);
                const paa = safeValue(player, '3paa', 0);
                const pes = safeValue(player, '3pes', 0);
                const total3pm = safeValue(player, 'total_3pm', 0);
                const total3pa = safeValue(player, 'total_3pa', 0);
                
                const vt3pm = safeValue(player, 'very_tight_3pm', 0);
                const vt3pa = safeValue(player, 'very_tight_3pa', 0);
                const vt3pct = safeValue(player, 'very_tight_3p_pct', 0);
                const vtfreq = safeValue(player, 'very_tight_freq', 0);
                
                const t3pm = safeValue(player, 'tight_3pm', 0);
                const t3pa = safeValue(player, 'tight_3pa', 0);
                const t3pct = safeValue(player, 'tight_3p_pct', 0);
                const tfreq = safeValue(player, 'tight_freq', 0);
                
                const o3pm = safeValue(player, 'open_3pm', 0);
                const o3pa = safeValue(player, 'open_3pa', 0);
                const o3pct = safeValue(player, 'open_3p_pct', 0);
                const ofreq = safeValue(player, 'open_freq', 0);
                
                const wo3pm = safeValue(player, 'wide_open_3pm', 0);
                const wo3pa = safeValue(player, 'wide_open_3pa', 0);
                const wo3pct = safeValue(player, 'wide_open_3p_pct', 0);
                const wofreq = safeValue(player, 'wide_open_freq', 0);
                
                // Create player photo HTML
                let photoHTML = '';
                if (playerId) {
                    photoHTML = `<img src="https://cdn.nba.com/headshots/nba/latest/260x190/${playerId}.png" 
                                     class="player-photo" 
                                     onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                                <span class="player-photo-placeholder" style="display:none;"></span>`;
                } else {
                    photoHTML = '<span class="player-photo-placeholder"></span>';
                }
                
                row.innerHTML = `
                    <td class="rank">${index + 1}</td>
                    <td class="player-name">
                        <div class="player-cell">
                            ${photoHTML}
                            <span class="player-name-link" data-player="${playerName}" style="cursor: pointer; color: #2196F3;">${playerName}</span>
                        </div>
                    </td>
                    <td class="stat-value" style="background-color: #e1f5fe; font-weight: bold;">${pes.toFixed(2)}</td>
                    <td class="stat-value" style="background-color: #fff9c4; font-weight: bold;">${oe >= 0 ? '+' : ''}${oe.toFixed(2)}%</td>
                    <td class="stat-value" style="background-color: #f3e5f5; font-weight: bold;">${paa.toFixed(2)}</td>
                    <td class="stat-value">${total3pm}</td>
                    <td class="stat-value">${total3pa}</td>
                    <td class="stat-value very-tight">${vt3pm}</td>
                    <td class="stat-value very-tight">${vt3pa}</td>
                    <td class="stat-value very-tight pct">${vt3pct.toFixed(1)}%</td>
                    <td class="stat-value very-tight freq">${vtfreq.toFixed(1)}%</td>
                    <td class="stat-value tight">${t3pm}</td>
                    <td class="stat-value tight">${t3pa}</td>
                    <td class="stat-value tight pct">${t3pct.toFixed(1)}%</td>
                    <td class="stat-value tight freq">${tfreq.toFixed(1)}%</td>
                    <td class="stat-value open">${o3pm}</td>
                    <td class="stat-value open">${o3pa}</td>
                    <td class="stat-value open pct">${o3pct.toFixed(1)}%</td>
                    <td class="stat-value open freq">${ofreq.toFixed(1)}%</td>
                    <td class="stat-value wide-open">${wo3pm}</td>
                    <td class="stat-value wide-open">${wo3pa}</td>
                    <td class="stat-value wide-open pct">${wo3pct.toFixed(1)}%</td>
                    <td class="stat-value wide-open freq">${wofreq.toFixed(1)}%</td>
                `;
                tbody.appendChild(row);
            });
            
            // Add click handlers for player names
            document.querySelectorAll('.player-name-link').forEach(link => {
                link.addEventListener('click', function() {
                    const playerName = this.getAttribute('data-player');
                    showMainView('player-profile');
                    selectPlayerProfile(playerName);
                });
            });
        }

        function sortTable(column) {
            const headers = document.querySelectorAll('th.sortable');
            
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'desc';
            }

            headers.forEach(header => {
                header.classList.remove('sort-asc', 'sort-desc');
            });

            const activeHeader = document.querySelector(`th[data-column="${column}"]`);
            if (activeHeader) {
                activeHeader.classList.add(sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
            }

            currentData.sort((a, b) => {
                if (!a || !b) return 0;
                let aVal, bVal;
                if (column === 'rank') return 0;
                else if (column === 'player') {
                    aVal = safeValue(a, column, '').toString().toLowerCase();
                    bVal = safeValue(b, column, '').toString().toLowerCase();
                    return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
                } else {
                    aVal = safeValue(a, column, 0);
                    bVal = safeValue(b, column, 0);
                    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
                }
            });

            renderTable(currentData);
        }

        function filterTable() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const minAttempts = parseInt(document.getElementById('minAttempts').value) || 0;
            const seasonData = allSeasonData[currentSeason] || [];
            
            // Apply qualification minimums
            const isCareer = currentSeason === 'Career';
            const qualMin = isCareer ? 250 : seasonQualMin(currentSeason); // 250 3PM for career, 82 3PA for season (pro-rated in progress)
            
            currentData = seasonData.filter(player => {
                if (!player) return false;
                
                // Check qualification
                const qualStat = isCareer ? safeValue(player, 'total_3pm', 0) : safeValue(player, 'total_3pa', 0);
                const meetsQual = qualStat >= qualMin;
                
                // Check search and min attempts
                const playerName = safeValue(player, 'player', '').toString().toLowerCase();
                const attempts = safeValue(player, 'total_3pa', 0);
                const matchesSearch = playerName.includes(searchTerm);
                const matchesAttempts = attempts >= minAttempts;
                
                return meetsQual && matchesSearch && matchesAttempts;
            });

            if (sortColumn) {
                sortTable(sortColumn);
            } else {
                renderTable(currentData);
            }
        }

        function changeSeason() {
            currentSeason = document.getElementById('seasonSelect').value;
            filterTable();
        }

        document.querySelectorAll('th.sortable').forEach(header => {
            header.addEventListener('click', () => {
                const column = header.getAttribute('data-column');
                sortTable(column);
            });
        });

        document.getElementById('search').addEventListener('input', filterTable);
        document.getElementById('minAttempts').addEventListener('input', filterTable);
        document.getElementById('seasonSelect').addEventListener('change', changeSeason);
        document.getElementById('vizSeasonSelect').addEventListener('change', changeVizSeason);
        document.getElementById('playerFilter').addEventListener('input', handlePlayerSearch);
        
        function changeVizSeason() {
            currentVizSeason = document.getElementById('vizSeasonSelect').value;
            selectedPlayers = [];
            updateSelectedPlayers();
            
            // Rebuild all charts
            Object.keys(charts).forEach(key => {
                if (charts[key]) {
                    charts[key].destroy();
                    delete charts[key];
                }
            });
            
            // Recreate the currently visible chart
            const activeTab = document.querySelector('.viz-tab.active');
            if (activeTab) {
                const vizText = activeTab.textContent.toLowerCase().replace(/\s+/g, '').replace(/[^a-z]/g, '');
                if (vizText.includes('p%oevs') || vizText.includes('volume')) {
                    createChart('scatter');
                } else if (vizText.includes('paavs') || vizText.includes('3pes')) {
                    createChart('metrics');
                } else if (vizText.includes('shotdist')) {
                    createChart('distribution');
                } else if (vizText.includes('efficiency')) {
                    createChart('efficiency');
                } else if (vizText.includes('best3pes')) {
                    createChart('best3pes');
                } else if (vizText.includes('cumulative')) {
                    createChart('cumulative');
                }
            }
        }
        
        function handlePlayerSearch() {
            const searchTerm = document.getElementById('playerFilter').value.toLowerCase();
            const suggestions = document.getElementById('playerSuggestions');
            
            if (searchTerm.length < 2) {
                suggestions.style.display = 'none';
                return;
            }
            
            const seasonData = allSeasonData[currentVizSeason] || [];
            const matches = seasonData
                .filter(p => safeValue(p, 'player', '').toLowerCase().includes(searchTerm))
                .slice(0, 10);
            
            if (matches.length > 0) {
                suggestions.innerHTML = matches.map(p => 
                    `<div style="padding: 8px; cursor: pointer; hover: background-color: #f0f0f0;" 
                          onclick="addPlayer('${safeValue(p, 'player', '').replace(/'/g, "\\'")}')">${safeValue(p, 'player', '')}</div>`
                ).join('');
                suggestions.style.display = 'block';
            } else {
                suggestions.style.display = 'none';
            }
        }
        
        function addPlayer(playerName) {
            if (!selectedPlayers.includes(playerName) && selectedPlayers.length < 5) {
                selectedPlayers.push(playerName);
                updateSelectedPlayers();
                document.getElementById('playerFilter').value = '';
                document.getElementById('playerSuggestions').style.display = 'none';
                
                // Rebuild current chart
                const activeViz = document.querySelector('.viz-tab.active');
                if (activeViz) {
                    const vizText = activeViz.textContent.toLowerCase().replace(/\s+/g, '').replace(/[^a-z]/g, '');
                    if (vizText.includes('efficiency')) {
                        if (charts.efficiency) charts.efficiency.destroy();
                        createChart('efficiency');
                    }
                }
            }
        }
        
        function removePlayer(playerName) {
            selectedPlayers = selectedPlayers.filter(p => p !== playerName);
            updateSelectedPlayers();
            
            // Rebuild current chart
            const activeViz = document.querySelector('.viz-tab.active');
            if (activeViz) {
                const vizText = activeViz.textContent.toLowerCase().replace(/\s+/g, '').replace(/[^a-z]/g, '');
                if (vizText.includes('efficiency')) {
                    if (charts.efficiency) charts.efficiency.destroy();
                    createChart('efficiency');
                }
            }
        }
        
        function updateSelectedPlayers() {
            const container = document.getElementById('selectedPlayers');
            container.innerHTML = selectedPlayers.map(name => 
                `<div class="player-badge">${name}<button onclick="removePlayer('${name.replace(/'/g, "\\'")}')">×</button></div>`
            ).join('');
        }

        populateSeasonSelector();
        populatePlayerProfileDropdown();
        filterTable();
        sortTable('3p_pct_oe');
        
        // Last updated = when the scraper last ran (embedded at build time)
        const updatedAt = new Date(LAST_UPDATED);
        const options = { year: 'numeric', month: 'long', day: 'numeric', timeZone: 'America/New_York' };
        document.getElementById('lastUpdatedDate').textContent = `Last Updated: ${updatedAt.toLocaleDateString('en-US', options)}`;
        
        // Main view switching
        function showMainView(viewName) {
            document.querySelectorAll('.main-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.main-view').forEach(view => view.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(viewName + '-view').classList.add('active');
            
            // If switching to visualizations, create charts if needed
            if (viewName === 'visualizations' && !charts.scatter) {
                createChart('scatter');
            }
        }
        
        // Visualization Functions
        let charts = {};
        
        function showViz(vizId) {
            document.querySelectorAll('.viz-tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.viz-panel').forEach(panel => panel.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(vizId + '-viz').classList.add('active');
            
            // Show/hide and enable/disable controls based on viz type
            const playerFilterContainer = document.getElementById('playerFilterContainer');
            const vizSeasonSelect = document.getElementById('vizSeasonSelect');
            
            if (vizId === 'efficiency') {
                playerFilterContainer.style.display = 'block';
            } else {
                playerFilterContainer.style.display = 'none';
            }
            
            // Lock to Career for Best 3PES and Cumulative
            if (vizId === 'best3pes' || vizId === 'cumulative') {
                vizSeasonSelect.value = 'Career';
                vizSeasonSelect.disabled = true;
                currentVizSeason = 'Career';
            } else {
                vizSeasonSelect.disabled = false;
            }
            
            if (!charts[vizId]) {
                createChart(vizId);
            }
        }
        
        function createChart(vizId) {
            const seasonData = allSeasonData[currentVizSeason] || [];
            const qualifiedPlayers = seasonData.filter(p => {
                const isCareer = currentVizSeason === 'Career';
                const threshold = isCareer ? 250 : seasonQualMin(currentVizSeason);
                const stat = isCareer ? safeValue(p, 'total_3pm', 0) : safeValue(p, 'total_3pa', 0);
                return stat >= threshold;
            });
            
            if (vizId === 'scatter') {
                createScatterChart(qualifiedPlayers);
            } else if (vizId === 'metrics') {
                createMetricsChart(qualifiedPlayers);
            } else if (vizId === 'efficiency') {
                createEfficiencyChart(qualifiedPlayers);
            } else if (vizId === 'best3pes') {
                createBest3PESChart();
            } else if (vizId === 'cumulative') {
                createCumulativeChart();
            }
        }
        
        // Helper function for mobile-responsive chart options
        function isMobile() {
            return window.innerWidth <= 768;
        }
        
        function getMobileChartOptions() {
            if (isMobile()) {
                return {
                    titleSize: 11,
                    legendSize: 9,
                    axisLabelSize: 9,
                    axisTitleSize: 10,
                    aspectRatio: 1.3, // Changed from 1.2 to be slightly wider
                    legendDisplay: false
                };
            }
            return {
                titleSize: 16,
                legendSize: 12,
                axisLabelSize: 11,
                axisTitleSize: 12,
                aspectRatio: 2,
                legendDisplay: true
            };
        }
        
        function createScatterChart(players) {
            const ctx = document.getElementById('scatterChart').getContext('2d');
            
            if (!players || players.length === 0) {
                ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                ctx.font = '16px Arial';
                ctx.fillStyle = '#666';
                ctx.textAlign = 'center';
                ctx.fillText('No qualified players for this season', ctx.canvas.width / 2, ctx.canvas.height / 2);
                return;
            }
            
            const data = players.map(p => ({
                x: safeValue(p, 'total_3pa', 0),
                y: safeValue(p, '3p_pct_oe', 0),
                label: safeValue(p, 'player', 'Unknown'),
                playerId: safeValue(p, 'player_id', null)
            }));
            
            const trendlineData = calculateTrendline(data);
            const mobileOpts = getMobileChartOptions();
            
            charts.scatter = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: '3P%OE vs Volume',
                        data: data,
                        backgroundColor: 'rgba(33, 150, 243, 0.6)',
                        borderColor: 'rgba(33, 150, 243, 1)',
                        borderWidth: 1,
                        pointRadius: isMobile() ? 3 : 5,
                        pointHoverRadius: isMobile() ? 5 : 8
                    }, {
                        label: 'Trend',
                        data: trendlineData,
                        type: 'line',
                        borderColor: 'rgba(244, 67, 54, 0.8)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: mobileOpts.aspectRatio,
                    plugins: {
                        title: {
                            display: true,
                            text: isMobile() ? '3P%OE vs 3PA' : `3P% Over Expected vs 3-Point Attempts (${currentVizSeason})`,
                            font: { size: mobileOpts.titleSize }
                        },
                        legend: {
                            display: mobileOpts.legendDisplay,
                            labels: { font: { size: mobileOpts.legendSize } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const point = context.raw;
                                    return [
                                        point.label,
                                        `3PA: ${point.x}`,
                                        `3P%OE: ${point.y >= 0 ? '+' : ''}${point.y.toFixed(2)}%`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            title: { 
                                display: true, 
                                text: isMobile() ? '3PA' : '3-Point Attempts',
                                font: { size: mobileOpts.axisTitleSize }
                            },
                            ticks: { font: { size: mobileOpts.axisLabelSize } },
                            beginAtZero: true
                        },
                        y: {
                            title: { 
                                display: true, 
                                text: isMobile() ? '3P%OE' : '3P% Over Expected',
                                font: { size: mobileOpts.axisTitleSize }
                            },
                            ticks: { font: { size: mobileOpts.axisLabelSize } },
                            grid: { color: (context) => context.tick.value === 0 ? '#000' : '#e0e0e0' }
                        }
                    }
                }
            });
        }
        
        function createMetricsChart(players) {
            const ctx = document.getElementById('metricsChart').getContext('2d');
            
            if (!players || players.length === 0) {
                ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
                ctx.font = '16px Arial';
                ctx.fillStyle = '#666';
                ctx.textAlign = 'center';
                ctx.fillText('No qualified players for this season', ctx.canvas.width / 2, ctx.canvas.height / 2);
                return;
            }
            
            const data = players.map(p => ({
                x: safeValue(p, '3paa', 0),
                y: safeValue(p, '3pes', 0),
                label: safeValue(p, 'player', 'Unknown')
            }));
            
            const trendlineData = calculateTrendline(data);
            const mobileOpts = getMobileChartOptions();
            
            charts.metrics = new Chart(ctx, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: '3PAA vs 3PES',
                        data: data,
                        backgroundColor: 'rgba(156, 39, 176, 0.6)',
                        borderColor: 'rgba(156, 39, 176, 1)',
                        borderWidth: 1,
                        pointRadius: isMobile() ? 3 : 5,
                        pointHoverRadius: isMobile() ? 5 : 8
                    }, {
                        label: 'Trend',
                        data: trendlineData,
                        type: 'line',
                        borderColor: 'rgba(244, 67, 54, 0.8)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointRadius: 0,
                        pointHoverRadius: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: mobileOpts.aspectRatio,
                    plugins: {
                        title: {
                            display: true,
                            text: isMobile() ? '3PAA vs 3PES' : `3PAA (Total Value) vs 3PES (Volume-Adjusted) - ${currentVizSeason}`,
                            font: { size: mobileOpts.titleSize }
                        },
                        legend: {
                            display: mobileOpts.legendDisplay,
                            labels: { font: { size: mobileOpts.legendSize } }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const point = context.raw;
                                    return [
                                        point.label,
                                        `3PAA: ${point.x.toFixed(2)}`,
                                        `3PES: ${point.y.toFixed(2)}`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        x: { 
                            title: { 
                                display: true, 
                                text: isMobile() ? '3PAA' : '3PAA (3-Point Above Average)',
                                font: { size: mobileOpts.axisTitleSize }
                            },
                            ticks: { font: { size: mobileOpts.axisLabelSize } }
                        },
                        y: { 
                            title: { 
                                display: true, 
                                text: isMobile() ? '3PES' : '3PES (3-Point Efficiency Score)',
                                font: { size: mobileOpts.axisTitleSize }
                            },
                            ticks: { font: { size: mobileOpts.axisLabelSize } }
                        }
                    }
                }
            });
        }
        
        function createDistributionChart(players) {
            const ctx = document.getElementById('distributionChart').getContext('2d');
            
            let playersToShow;
            if (selectedPlayers.length > 0) {
                playersToShow = players.filter(p => selectedPlayers.includes(safeValue(p, 'player', '')));
            } else {
                playersToShow = players.slice(0, 10);
            }
            
            const labels = playersToShow.map(p => safeValue(p, 'player', 'Unknown'));
            
            charts.distribution = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Very Tight (0-2 ft)',
                            data: playersToShow.map(p => safeValue(p, 'very_tight_freq', 0)),
                            backgroundColor: 'rgba(244, 67, 54, 0.7)'
                        },
                        {
                            label: 'Tight (2-4 ft)',
                            data: playersToShow.map(p => safeValue(p, 'tight_freq', 0)),
                            backgroundColor: 'rgba(255, 152, 0, 0.7)'
                        },
                        {
                            label: 'Open (4-6 ft)',
                            data: playersToShow.map(p => safeValue(p, 'open_freq', 0)),
                            backgroundColor: 'rgba(76, 175, 80, 0.7)'
                        },
                        {
                            label: 'Wide Open (6+ ft)',
                            data: playersToShow.map(p => safeValue(p, 'wide_open_freq', 0)),
                            backgroundColor: 'rgba(33, 150, 243, 0.7)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2,
                    plugins: {
                        title: {
                            display: true,
                            text: selectedPlayers.length > 0 ? 'Shot Distribution by Defender Distance (Selected Players)' : 'Shot Distribution by Defender Distance (Top 10 Players)',
                            font: { size: 16 }
                        }
                    },
                    scales: {
                        x: { stacked: true },
                        y: { 
                            stacked: true,
                            title: { display: true, text: 'Percentage of Shots (%)' },
                            max: 100
                        }
                    }
                }
            });
        }
        
        function createEfficiencyChart(players) {
            const ctx = document.getElementById('efficiencyChart').getContext('2d');
            
            let playersToShow;
            if (selectedPlayers.length > 0) {
                playersToShow = players.filter(p => selectedPlayers.includes(safeValue(p, 'player', '')));
            } else {
                playersToShow = players.slice(0, 5);
            }
            
            const labels = ['Very Tight', 'Tight', 'Open', 'Wide Open'];
            
            const datasets = playersToShow.map((p, idx) => {
                const colors = [
                    'rgba(33, 150, 243, 0.6)',
                    'rgba(156, 39, 176, 0.6)',
                    'rgba(76, 175, 80, 0.6)',
                    'rgba(255, 152, 0, 0.6)',
                    'rgba(244, 67, 54, 0.6)'
                ];
                
                return {
                    label: safeValue(p, 'player', 'Unknown'),
                    data: [
                        safeValue(p, 'very_tight_3p_pct', 0),
                        safeValue(p, 'tight_3p_pct', 0),
                        safeValue(p, 'open_3p_pct', 0),
                        safeValue(p, 'wide_open_3p_pct', 0)
                    ],
                    attempts: [
                        safeValue(p, 'very_tight_3pa', 0),
                        safeValue(p, 'tight_3pa', 0),
                        safeValue(p, 'open_3pa', 0),
                        safeValue(p, 'wide_open_3pa', 0)
                    ],
                    makes: [
                        safeValue(p, 'very_tight_3pm', 0),
                        safeValue(p, 'tight_3pm', 0),
                        safeValue(p, 'open_3pm', 0),
                        safeValue(p, 'wide_open_3pm', 0)
                    ],
                    borderColor: colors[idx % colors.length].replace('0.6', '1'),
                    backgroundColor: colors[idx % colors.length],
                    borderWidth: 2
                };
            });
            
            charts.efficiency = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: datasets
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 1.5,
                    plugins: {
                        title: {
                            display: true,
                            text: selectedPlayers.length > 0 ? '3P% by Defender Distance (Selected Players)' : '3P% by Defender Distance (Top 5 Players)',
                            font: { size: 16 }
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const dataset = context.dataset;
                                    const idx = context.dataIndex;
                                    return [
                                        `${dataset.label}: ${context.parsed.r.toFixed(1)}%`,
                                        `${dataset.makes[idx]}/${dataset.attempts[idx]} 3PT`
                                    ];
                                }
                            }
                        }
                    },
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: { stepSize: 20 }
                        }
                    }
                }
            });
        }
        
        function createBest3PESChart() {
            const container = document.getElementById('best3pesTable');
            
            // Collect all individual season performances (exclude Career)
            const allSeasonPerformances = [];
            Object.keys(allSeasonData).forEach(season => {
                if (season !== 'Career') {
                    const seasonPlayers = allSeasonData[season] || [];
                    seasonPlayers.forEach(p => {
                        const isValid = safeValue(p, 'total_3pa', 0) >= 82;
                        if (isValid) {
                            allSeasonPerformances.push({
                                player: safeValue(p, 'player', 'Unknown'),
                                playerId: safeValue(p, 'player_id', null),
                                season: season,
                                pes: safeValue(p, '3pes', 0),
                                oe: safeValue(p, '3p_pct_oe', 0),
                                paa: safeValue(p, '3paa', 0),
                                attempts: safeValue(p, 'total_3pa', 0),
                                makes: safeValue(p, 'total_3pm', 0)
                            });
                        }
                    });
                }
            });
            
            // Sort by 3PES and take top 25
            const top25 = allSeasonPerformances
                .sort((a, b) => b.pes - a.pes)
                .slice(0, 25);
            
            const maxPES = top25[0].pes;
            const maxPAA = Math.max(...top25.map(p => p.paa));
            
            let html = `
                <table class="best3pes-table">
                    <thead>
                        <tr>
                            <th class="rank-col">#</th>
                            <th class="player-col">Player</th>
                            <th class="stat-col">Season</th>
                            <th class="stat-col">3PES</th>
                            <th class="stat-col">3P%OE</th>
                            <th class="stat-col">3PM/3PA</th>
                            <th style="min-width: 200px;">3PES Visualization</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            top25.forEach((p, idx) => {
                const pesWidth = (p.pes / maxPES * 100).toFixed(1);
                const paaWidth = (p.paa / maxPAA * 100).toFixed(1);
                
                let photoHTML = '';
                if (p.playerId) {
                    photoHTML = `<img src="https://cdn.nba.com/headshots/nba/latest/260x190/${p.playerId}.png" 
                                     onError="this.style.display='none'"
                                     style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover; margin-right: 10px; vertical-align: middle; border: 2px solid #ddd;">`;
                } else {
                    photoHTML = '<span style="width: 40px; height: 40px; border-radius: 50%; background-color: #e0e0e0; display: inline-block; margin-right: 10px; vertical-align: middle;"></span>';
                }
                
                html += `
                    <tr>
                        <td class="rank-col">${idx + 1}</td>
                        <td class="player-col">
                            <div style="display: flex; align-items: center;">
                                ${photoHTML}
                                <span class="best3pes-player-link" data-player="${p.player}" style="font-weight: bold; cursor: pointer; color: #2196F3;">${p.player}</span>
                            </div>
                        </td>
                        <td class="stat-col">${p.season}</td>
                        <td class="stat-col" style="font-weight: bold; color: #2196F3;">${p.pes.toFixed(2)}</td>
                        <td class="stat-col">${p.oe >= 0 ? '+' : ''}${p.oe.toFixed(2)}%</td>
                        <td class="stat-col">${p.makes}/${p.attempts}</td>
                        <td>
                            <div class="bar-viz" style="--width: ${pesWidth}%;">
                                <span class="bar-label">${p.pes.toFixed(1)}</span>
                            </div>
                        </td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
            `;
            
            container.innerHTML = html;
            
            // Add click handlers for player names in Best 3PES table
            document.querySelectorAll('.best3pes-player-link').forEach(link => {
                link.addEventListener('click', function() {
                    const playerName = this.getAttribute('data-player');
                    showMainView('player-profile');
                    selectPlayerProfile(playerName);
                });
            });
            
            charts.best3pes = true; // Mark as created
        }
        
        function createCumulativeChart() {
            const ctx = document.getElementById('cumulativeChart').getContext('2d');
            
            // Get top 25 career leaders by 3PAA
            const careerData = allSeasonData['Career'] || [];
            const qualifiedPlayers = careerData
                .filter(p => safeValue(p, 'total_3pm', 0) >= 250)
                .sort((a, b) => safeValue(b, '3paa', 0) - safeValue(a, '3paa', 0))
                .slice(0, 25);
            
            const seasonsToShow = Object.keys(allSeasonData).filter(s => s !== 'Career').sort();
            
            // Map seasons to numeric years for proper ordering
            const seasonToYear = {};
            seasonsToShow.forEach(s => { seasonToYear[s] = parseInt(s.slice(0, 4)); });
            
            const colors = [
                '#2196F3', '#9C27B0', '#4CAF50', '#FF9800', '#F44336',
                '#00BCD4', '#E91E63', '#8BC34A', '#FF5722', '#3F51B5',
                '#009688', '#FFC107', '#795548', '#607D8B', '#CDDC39',
                '#FF4081', '#00E676', '#FFD600', '#FF6E40', '#651FFF',
                '#00B8D4', '#AEEA00', '#FF3D00', '#6200EA', '#00C853'
            ];
            
            const datasets = qualifiedPlayers.map((player, idx) => {
                const playerName = safeValue(player, 'player', 'Unknown');
                
                // Build cumulative data across seasons
                const cumulativeData = [];
                let cumPAA = 0;
                
                seasonsToShow.forEach(season => {
                    const seasonData = allSeasonData[season] || [];
                    const playerSeason = seasonData.find(p => safeValue(p, 'player', '') === playerName);
                    
                    if (playerSeason && safeValue(playerSeason, 'total_3pa', 0) >= seasonQualMin(season)) {
                        cumPAA += safeValue(playerSeason, '3paa', 0);
                        cumulativeData.push({
                            x: seasonToYear[season],
                            y: cumPAA,
                            season: season
                        });
                    } else if (cumulativeData.length > 0) {
                        // Continue line at same value if player didn't play that season
                        cumulativeData.push({
                            x: seasonToYear[season],
                            y: cumPAA,
                            season: season
                        });
                    }
                });
                
                return {
                    label: playerName,
                    data: cumulativeData,
                    borderColor: colors[idx % colors.length],
                    backgroundColor: colors[idx % colors.length] + '33',
                    borderWidth: 2,
                    tension: 0.1,
                    fill: false,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: colors[idx % colors.length],
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2
                };
            }).filter(d => d.data.length > 0);
            
            charts.cumulative = new Chart(ctx, {
                type: 'line',
                data: { datasets: datasets },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2,
                    interaction: {
                        mode: 'nearest',
                        axis: 'x',
                        intersect: false
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: 'Cumulative 3PAA Over Career (Top 25 Career Leaders)',
                            font: { size: 16 }
                        },
                        tooltip: {
                            mode: 'nearest',
                            intersect: false,
                            callbacks: {
                                title: function(context) {
                                    if (context[0].raw.season) {
                                        return context[0].raw.season;
                                    }
                                    const year = context[0].parsed.x;
                                    return `${year}-${(year + 1).toString().slice(2)}`;
                                },
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}`;
                                }
                            }
                        },
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        x: {
                            type: 'linear',
                            min: 2013,
                            max: ''' + str(latest_year + 1) + ''',
                            title: { display: true, text: 'Season' },
                            ticks: {
                                stepSize: 1,
                                callback: function(value) {
                                    const year = Math.floor(value);
                                    return `${year}-${(year + 1).toString().slice(2)}`;
                                }
                            }
                        },
                        y: {
                            title: { display: true, text: 'Cumulative 3PAA' },
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Update charts when season changes
        const originalChangeSeason = changeSeason;
        changeSeason = function() {
            originalChangeSeason();
            // Reset charts so they rebuild with new data
            Object.keys(charts).forEach(key => {
                if (charts[key]) {
                    charts[key].destroy();
                    delete charts[key];
                }
            });
            // Recreate the currently active chart
            const activeViz = document.querySelector('.viz-tab.active');
            if (activeViz) {
                const vizId = activeViz.textContent.toLowerCase().replace(/[^a-z]/g, '');
                const vizMap = {
                    'p%oevvolume': 'scatter',
                    'paavs3pes': 'metrics',
                    'shotdistribution': 'distribution',
                    'efficiencybydistance': 'efficiency'
                };
                Object.keys(vizMap).forEach(key => {
                    if (activeViz.textContent.toLowerCase().replace(/[^a-z]/g, '').includes(key.substring(0, 10))) {
                        createChart(vizMap[key]);
                    }
                });
            }
        };
    </script>
    
    <!-- Site Footer -->
    <div class="site-footer">
        <div style="font-size: 18px; font-weight: bold; margin-bottom: 10px;">3point.app</div>
        <div style="font-size: 13px; color: #cbd5e0; margin-bottom: 15px;">Advanced 3-Point Shooting Analytics</div>
        <div class="footer-links">
            <a href="mailto:deeprangedata@gmail.com">Contact</a> | 
            <a href="mailto:deeprangedata@gmail.com">Advertise</a> | 
            <a href="mailto:deeprangedata@gmail.com">Data Licensing</a> | 
            <a href="#" onclick="showTerms(); return false;">Terms of Service</a>
        </div>
        <div style="font-size: 12px; color: #a0aec0; margin-top: 15px;">
            © 2026 3point.app | 3PES, 3PAA, and 3P%OE are proprietary metrics<br>
            All statistics and data are provided for informational purposes only. No redistribution permitted.
        </div>
    </div>
    
    <!-- Terms of Service Modal -->
    <div id="termsModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; padding: 40px; overflow-y: auto;">
        <div style="max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px;">
            <h2 style="margin-bottom: 20px; color: #1a365d;">Terms of Service</h2>
            <div style="line-height: 1.8; color: #333;">
                <h3 style="margin-top: 20px; color: #1a365d;">1. Proprietary Metrics</h3>
                <p>3PES (3-Point Efficiency Score), 3PAA (3-Point Above Average), and 3P%OE (3-Point Percentage Over Expected) are proprietary statistical metrics developed by 3point.app. These metrics and their calculation methodologies are the intellectual property of 3point.app.</p>
                
                <h3 style="margin-top: 20px; color: #1a365d;">2. Data Usage</h3>
                <p>All data, statistics, and visualizations provided on this website are for personal, non-commercial use only. You may not:</p>
                <ul style="margin: 10px 0 10px 30px;">
                    <li>Redistribute, republish, or reproduce the data in any form</li>
                    <li>Use automated tools to scrape or download bulk data</li>
                    <li>Present the data as your own work or analysis</li>
                    <li>Use the data for commercial purposes without a licensing agreement</li>
                </ul>
                
                <h3 style="margin-top: 20px; color: #1a365d;">3. Attribution</h3>
                <p>If you reference statistics from 3point.app in articles, social media, podcasts, or other media, you must provide clear attribution to 3point.app with a link to the website.</p>
                
                <h3 style="margin-top: 20px; color: #1a365d;">4. Commercial Licensing</h3>
                <p>For commercial use, data licensing, API access, or bulk data requests, please contact <a href="mailto:deeprangedata@gmail.com" style="color: #2196F3;">deeprangedata@gmail.com</a></p>
                
                <h3 style="margin-top: 20px; color: #1a365d;">5. Accuracy and Disclaimer</h3>
                <p>While we strive for accuracy, all data is provided "as is" without warranty. 3point.app is not responsible for decisions made based on this data. This is not gambling or fantasy sports advice.</p>
                
                <h3 style="margin-top: 20px; color: #1a365d;">6. Changes to Terms</h3>
                <p>We reserve the right to modify these terms at any time. Continued use of the website constitutes acceptance of updated terms.</p>
                
                <p style="margin-top: 30px; color: #64748b; font-size: 14px;">Last Updated: February 2026</p>
            </div>
            <button onclick="document.getElementById('termsModal').style.display='none'" 
                    style="margin-top: 30px; padding: 12px 30px; background-color: #1a365d; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                Close
            </button>
        </div>
    </div>
    
    <script>
        function showTerms() {
            document.getElementById('termsModal').style.display = 'block';
        }
    </script>
</body>
</html>'''

# Save the HTML
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print("\n✓ SUCCESS! Website created: index.html")
print("\nOpen index.html in your browser!")
print("You can switch between seasons (including Career stats) using the dropdown.")
