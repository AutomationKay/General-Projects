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
    
    # Preprocess the HTML to remove comment tags, making hidden tables visible
    html_content = response.text.replace('', '')
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the table, which is now visible to the parser
    table = soup.find(name="table", attrs={"id": table_id})
    
    if not table:
         raise ValueError(f"Table with id='{table_id}' not found after attempting to un-comment.")

    df = pd.read_html(StringIO(str(table)))[0]

    # Flatten multi-level headers if they exist
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel()
    
    # Drop the "Rk" and "Awards" columns to avoid conflicts, ignoring if it doesn't exist
    df.drop(columns=['Rk', 'Awards'], inplace=True, errors='ignore')

    return df



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
    advanced_df = fetch_table(advanced_url, "advanced")

    # Filter out repeated header rows
    per_game_df = per_game_df[per_game_df.Age.notna()]
    advanced_df = advanced_df[advanced_df.Age.notna()]

    # Renaming the "PTS" column to "PPG" as it's the more common term
    if "PTS" in per_game_df.columns:
        per_game_df.rename(columns={"PTS": "PPG"}, inplace=True)

    # DEBUGGING
    # print("\n\n--- Per Game DF Info ---")
    # print(per_game_df.columns)
    # print(per_game_df.head(3))

    # print("\n--- Advanced DF Info ---")
    # print(advanced_df.columns)
    # print(advanced_df.head(3))

    # Dropping columns from advanced table due to redundancy
    cols_to_drop = ["G", "GS", "MP"]
    advanced_df.drop(columns=[col for col in cols_to_drop if col in advanced_df.columns], inplace=True)
    
    # Merge DataFrames on shared columns
    merged_df = pd.merge(per_game_df, advanced_df,
                         on=["Player", "Pos", "Age", "Team"]
                         )
    
    # Award winners 
    awards = get_awards(year)
    merged_df["is_MVP"] = merged_df["Player"] == awards.get("MVP", "")
    merged_df["is_DPOY"] = merged_df["Player"] == awards.get("DPOY", "")
    
    # Scoring leader
    ppg_leader = merged_df.loc[merged_df["PPG"].astype(float).idxmax(), "Player"]
    merged_df["is_PPG_Leader"] = merged_df["Player"] == ppg_leader
    
    return merged_df

def scrape_combined_team_stats(year: int) -> pd.DataFrame:
    """
    Scrapes regular season team stats along with win-loss records

    Args:
        year (int): Int value represneting the year being saved

    Returns:
        pd.DataFrame: DataFrame containing team stats 
    """
   
    url = f"https://www.basketball-reference.com/leagues/NBA_{year}.html"
    
   # Use the fetch_table function to get both team stat tables
    per_game_df = fetch_table(url, "per_game-team")
    advanced_df = fetch_table(url, "advanced-team")
    
    # Filter out the "League Average" row from both tables
    per_game_df = per_game_df[per_game_df["Team"] != "League Average"].reset_index(drop=True)
    advanced_df = advanced_df[advanced_df["Team"] != "League Average"].reset_index(drop=True)

    # Drop redundant columns from the advanced table to prepare for a clean merge
    advanced_df.drop(columns=['G', 'MP'], inplace=True, errors='ignore')
    
    # Merge based on team name
    team_df = pd.merge(per_game_df, advanced_df, on="Team")
                       
    return team_df