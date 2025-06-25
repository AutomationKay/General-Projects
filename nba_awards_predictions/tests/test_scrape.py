# tests/test_scrape.py

import pytest
from src.data.scrape import scrape_combined_stats, scrape_combined_team_stats

def test_scrape_combined_stats():
    df = scrape_combined_stats(2023)
    assert not df.empty, "Player stats dataframe should not be empty"
    assert "Player" in df.columns, "Missing 'Player' column"
    assert df["is_MVP"].dtype == bool, "'is_MVP' should be boolean"

def test_scrape_combined_team_stats():
    df = scrape_combined_team_stats(2023)
    assert not df.empty, "Team stats dataframe should not be empty"
    assert "Team" in df.columns, "Missing 'Team' column"
