#src/data/scrape.py

import requests
from bs4 import BeautifulSoup, Comment
import pandas as pd
from get_award_winners import get_awards
from io import StringIO
import time
import os


# Configuring session and headers to avoid 429 rate-limiting
session = requests.Session()
headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36"
}
session.headers.update(headers)
    

def fetch_table(url: str, table_id: str, pause: float = 6.0) ->pd.DataFrame:
    """
    Helper function to fetch a table from Basketball Reference then return a DataFrame

    Args:
        url (str): The URL needed for gather data
        table_id (str): The ID for each individual table to be used in the join process

    Returns:
        pd.DataFrame: A dataframe containing a layout to be filled with data for players and teams
    """
    print(f"Fetching table: {url} [{table_id}]")
    response = session.get(url)
    time.sleep(pause)
    
    if not response.ok:
        raise Exception(f"Failed to fetch data from {url}, status code {response.status_code}")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Attempt to find regular table
    table = soup.find(name="table", attrs={"id": table_id})
    
    if table:
        return pd.read_html(StringIO(str(table)))[0]

    # Otherwise, search in comment blocks
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if table_id in comment:
            try:
                comment_soup = BeautifulSoup(comment, "html.parser")
                table = comment_soup.find("table", attrs={"id": table_id})
                if table:
                    return pd.read_html(StringIO(str(table)))[0]
            except Exception as e:
                print(f"Failed to parse table in comment: {e}")

    raise ValueError(f"Table with id={table_id} not found (including comments)")


def scrape_combined_stats(year: int) -> pd.DataFrame:
    """
    Scrapes and merges player-per-game, player-advanced stats and team stats for the given NBA season

    Args:
        year (int): _description_

    Returns:
        pd.DataFrame: _description_
    """
    
    base_url = "https://www.basketball-reference.com/leagues"
    
    # Per-game Stats
    per_game_url = f"{base_url}/NBA_{year}_per_game.html"
    per_game_df = fetch_table(per_game_url, "per_game_stats")
    
    # Advanced stats
    advanced_url = f"{base_url}/NBA_{year}_advanced.html"
    advanced_df = fetch_table(advanced_url, "advanced_stats")
    
    # Dropping duplicate columns prior to merging
    columns_to_drop = ["Rk"]
    advanced_df = advanced_df.drop(columns=[col for col in columns_to_drop if col in advanced_df.columns])
    per_game_df = per_game_df.drop(columns=[col for col in columns_to_drop if col in per_game_df.columns])
    
    # Merge DataFrames on shared columns
    merged_df = pd.merge(per_game_df, advanced_df,
                         on=["Player", "Pos", "Age", "Tm"],
                         suffixes=("_per_game", "_adv"))
    
    # Award winners 
    awards = get_awards(year)
    merged_df["is_MVP"] = merged_df["Player"] == awards.get("MVP", "")
    merged_df["is_DPOY"] = merged_df["Player"] == awards.get("DPOY", "")
    
    # Scoring leader
    ppg_leader = merged_df.loc[merged_df["PTS_per_game"].astype(float).idxmax(), "Player"]
    merged_df["is_PPG_Leader"] = merged_df["Player"] == ppg_leader
    
    return merged_df

def scrape_combined_team_stats(year: int) -> pd.DataFrame:
    """
    Scrapes regular season team stats along with win-loss records

    Args:
        year (int): _description_

    Returns:
        pd.DataFrame: _description_
    """
   
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    
    print(f"Fetching team stats: {url}")
    response = session.get(url)
    time.sleep(3)
    
    if not response.ok:
        raise Exception(f"Failed to fetch team data for {year}")
    
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Per-game team stats
    per_game_table = soup.find(name="table", attrs={"id": "team-stats-per_game"})
    per_game_df = pd.read_html(str(per_game_table))[0]
    per_game_df = per_game_df[per_game_df["Team"] != "League Average"].reset_index(drop=True)
    
    # Advanced team stats
    advanced_table = soup.find(name="table", attrs={"id": "advanced-team"})
    advanced_df = pd.read_html(str(advanced_table))[0]
    advanced_df = advanced_df[advanced_df["Team"] != "League Average"].reset_index(drop=True)
    
    # Remove unneeded columns and duplicates
    drop_cols = [col for col in ["Rk"] if col in per_game_df.columns]
    per_game_df.drop(columns=drop_cols, inplace=True)
    advanced_df.drop(columns=drop_cols, inplace=True)
    
    # Merge based on team name
    team_df = pd.merge(per_game_df, advanced_df,
                       on="Team",
                       suffixes=("_per_game", "_adv")
                       )
    return team_df 
