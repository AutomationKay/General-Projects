# src/data/get_award_winners.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

def get_awards(year: int) -> dict:
    """
    Function for requesting data from Basketball Reference containing awards information 

    Args:
        year (int): The year in reference for finding stats

    Returns:
        dict: dictionary containing award winners
    """
    
    awards_url = f"https://www.basketball-reference.com/awards/awards_{year}.html"
    stats_url = f"https://www.basketball-reference.com/leagues/NBA_{year}_per_game.html"
    
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/114.0.0.0 Safari/537.36"
    }
    session.headers.update(headers)
    
    awards_resp = session.get(awards_url)
    stats_resp = session.get(stats_url)
    
    print(f"Fetching: {awards_url}")
    print(f"Fetching: {stats_url}")
    
    if not awards_resp.ok:
        print(f"Awards page failed for {year}: {awards_resp.status_code}")
        return {}

    if not stats_resp.ok:
        print(f"Stats page failed for {year}: {stats_resp.status_code}")
        return {}
    
    if not awards_resp.ok or not stats_resp.ok:
        raise Exception(f"Failed to retrieve awards or stats for year {year}")
    
    awards_soup = BeautifulSoup(awards_resp.content, "html.parser")
    
    def extract_winner(section_title):
        """
        Helper function to extract the winner of a particular award from Basketball Reference

        Args:
            section_title (string): String value assigned to the section 

        Returns:
            None
        """
        section = awards_soup.find("h2", string=section_title)
        if section and section.find_next("strong"):
            return section.find_next("strong").text.strip()
        return None
    
    mvp = extract_winner("NBA Most Valuable Player")
    dpoy = extract_winner("Defensive Player of the Year")
    
    # Extract PPG Leader
    ppg_leader = None
    try: 
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
    history = get_award_history(2010, 2025)
    with open("data/awards/award_winners.json", "w") as f:
        json.dump(history, f, indent=4)
    