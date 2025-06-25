# tests/test_preprocess.py

import pytest
import pandas as pd
from src.data.preprocessing import clean_player_data, clean_team_data

@pytest.fixture
def sample_player_data():
    return pd.DataFrame({
        "Player": ["LeBron James", "Kevin Durant", "LeBron James"],
        "PTS": [25, 27, 25],
        "is_MVP": [True, False, True]
    })

@pytest.fixture
def sample_team_data():
    return pd.DataFrame({
        "Team": ["LAL", "BKN", "LAL"],
        "W": [45, 50, 45]
    })

def test_clean_player_data(sample_player_data):
    df = clean_player_data(sample_player_data)
    assert df.duplicated().sum() == 0, "Should remove duplicate player rows"
    assert not df.isnull().any().any(), "Should not contain nulls"

def test_clean_team_data(sample_team_data):
    df = clean_team_data(sample_team_data)
    assert df.duplicated().sum() == 0, "Should remove duplicate team rows"
    assert "Team" in df.columns
