# updated_data.py

from scrape import scrape_combined_stats, scrape_combined_team_stats
import os
import pandas as pd
from datetime import datetime

RAW_DATA_PATH = "data/raw"
TEAM_DATA_PATH = "data/teams"

def save_season_data(year: int):
    # Player stats
    player_df = scrape_combined_stats(year)
    os.makedirs(RAW_DATA_PATH, exist_ok=True)
    player_df.to_csv(f"{RAW_DATA_PATH}/nba_combined_stats_{year}.csv", index=False)
    
    # Team stats
    team_df = scrape_combined_team_stats(year)
    os.makedirs(TEAM_DATA_PATH, exist_ok=True)
    team_df.to_csv(f"{TEAM_DATA_PATH}/team_combined_stats_{year}.csv", index=False)
    
    print (f"[{datetime.now()}] Saved player and team data for {year}")

if __name__ == "__main__":
    for year in range(2020, 2025):
        save_season_data(year)