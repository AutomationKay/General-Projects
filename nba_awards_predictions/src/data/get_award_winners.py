# src/data/get_award_winners.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

session = requests.Session()
headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36"
    }
session.headers.update(headers)


def _get_award_winner(url: str, table_id: str, year: int) -> str | None:
    """
    Helper function to scrape a specific award table for a given year.

    Args:
        url (str): The URL of the historical award page (MVP or DPOY).
        table_id (str): The HTML 'id' of the main data table (e.g., 'mvp').
        year (int): The target year for the award.

    Returns:
        str or None: The name of the award winner, or None if not found.
    """
    print(f"Fetching: {url} for {year} awards")
    try:
        response = session.get(url)
        time.sleep(10)  
        response.raise_for_status()
        
        html_content = response.text.replace('', '')
        soup = BeautifulSoup(html_content, 'html.parser')

        table = soup.find('table', id=table_id)
        
        if not table or not table.tbody:
            print(f"Could not find table with class '{table_id}' or its body.")
            return None

        # Seasons are formatted as '2019-20' for the year 2020
        season_to_find = f"{year - 1}-{str(year)[-2:]}"
        
        # Find the header row for the correct season
        for row in table.tbody.find_all("tr"):
            season_cell = row.find("th", {"data-stat": "season"})
            if season_cell:
                print(f"Checking season row: {season_cell.text.strip()}")
            if season_cell and season_cell.a and season_cell.a.text.strip() == season_to_find:
                player_cell = row.find("td", {"data-stat": "player"})
                if player_cell and player_cell.a:
                    return player_cell.a.text.strip()
    
        print(f"Could not find an entry for the {season_to_find} season in the table.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
    except Exception as e:
        print(f"An error occurred scraping {table_id} for {year}: {e}")
        
    print(f"Could not find a winner for {year} in the {table_id} table.")
    return None

def get_awards(year: int) -> dict:
    """
    Function for requesting data from Basketball Reference containing awards information 

    Args:
        year (int): The year in reference for finding stats

    Returns:
        dict: dictionary containing award winners
    """
    
    mvp_url = f"https://www.basketball-reference.com/awards/mvp.html"
    dpoy_url = f"https://www.basketball-reference.com/awards/dpoy.html"
    stats_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
    
    
    mvp = _get_award_winner(mvp_url, "mvp_NBA", year)
    dpoy = _get_award_winner(dpoy_url, "dpoy_NBA", year)

    # Extract PPG Leader
    ppg_leader = None
    try: 
        print(f"Fetching: {stats_url}")
        stats_resp = session.get(stats_url)
        time.sleep(10)
        stats_resp.raise_for_status()

        table = pd.read_html(stats_resp.text, attrs={"id": "per_game_stats"})[0]
        table = table[table["Player"] != "Player"]
        table["PTS"] = pd.to_numeric(table["PTS"], errors="coerce")
        table = table.dropna(subset=['PTS'])
        top_row = table.loc[table["PTS"].idxmax()]
        ppg_leader = top_row["Player"]
    except Exception as e:
        print(f"Failed to extract PPG leader for {year} : {e}")
    
    return {
        "MVP": mvp,
        "DPOY": dpoy,
        "PPG Leader": ppg_leader
    } 
    


def get_award_history(start_year: int, end_year: int) -> dict:
    """
    Function for matching awards given to each winner over prior NBA seasons

    Args:
        start_year (int): The year to begin sorting
        end_year (int): The year to stop sorting 

    Returns:
        dict: Dictionary containing MVP, DPOY winners and the player leading the league in PPG
    """
    award_history = {}
    for year in range(start_year, end_year +1):
        print(f"Scraping awards for {year}...")
        award_history[year] = get_awards(year)
        time.sleep(10) # Delay for 10 seconds between requests
    return award_history



if __name__ == "__main__":
    current_year = time.localtime().tm_year
    history = get_award_history(2010, current_year)
    with open("data/awards/award_winners.json", "w") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
    print("\nAward history has been saved to data/awards/award_winners.json")