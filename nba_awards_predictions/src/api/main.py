# src/api/main.py

import os
import torch
import joblib
import json
from fastapi import FastAPI, Depends
from src.api.security import verify_api_key
from src.api.schemas import PlayerStats, TeamStats, PredictionResponse
from src.api.model_definition import NBAAwardNet
import numpy as np
from glob import glob
from datetime import datetime


# -----------
# FASTAPI App
# -----------
app = FastAPI(title="NBA Awards Prediction API")

#  ---------------
# Helper Functions
# ----------------
def get_latest_model_dir(base_path: str, prefix: str) -> str:
    """
    Locate the most recent subdirectory under base_dir that contains the model name (e.g., MVP).
    """
    subdirs = [d for d in os.listdir(base_path) if d.startswith(prefix)]
    if not subdirs:
        raise FileNotFoundError(f"No model folder found for prefix '{prefix}'")
    subdirs.sort(
    key=lambda x: datetime.strptime(x.replace(f"{prefix}_leader_", "").replace(f"{prefix}_", ""), "%Y_%m_%d"),
    reverse=True
    )
    return os.path.join(base_path, subdirs[0])

def load_model_and_assets(model_dir: str, model_prefix: str):
    weights_path = os.path.join(model_dir, f"{model_prefix}_model_weights.pth")
    feature_path = os.path.join(model_dir, f"{model_prefix}_feature_list.json")
    scaler_path = os.path.join(model_dir, f"{model_prefix}_scaler.pkl")

    if not all(os.path.exists(p) for p in [weights_path, feature_path, scaler_path]):
        raise FileNotFoundError(f"Missing files in {model_dir} for model prefix {model_prefix}")

    with open(feature_path, "r") as f:
        feature_data = json.load(f)
        features = feature_data["features"]

    with open(scaler_path, "rb") as f:
        scaler = joblib.load(f)
    
    # Instantiate model and load weights
    input_size = len(features)
    model = NBAAwardNet(input_size)
    model.load_state_dict(torch.load(weights_path))
    model.eval()

    return model, features, scaler

def preprocess_input(data_dict, feature_list, scaler):
    try:
        ordered_values = [data_dict[feature] for feature in feature_list]
    except KeyError as e:
        raise ValueError(f"Missing feature: {e}")
    
    scaled_values = scaler.transform([ordered_values])
    return torch.tensor(scaled_values, dtype=torch.float32)

# --------------------------------
# Loading in all models and assets
# --------------------------------
base_dl_path = "models/dl"
try:
    mvp_model, mvp_features, mvp_scaler = load_model_and_assets(
        get_latest_model_dir(base_dl_path, "MVP"), "MVP"
    )
except Exception as e:
    print(f"[WARNING] Skipping MVP model due to error: {e}")
    mvp_model, mvp_features, mvp_scaler = None, None, None

try:
    # Load other models as usual
    dpoy_model, dpoy_features, dpoy_scaler = load_model_and_assets(
        get_latest_model_dir(base_dl_path, "dpoy"), "dpoy"
    )
except Exception as e:
    print(f"[WARNING] Skipping DPOY model due to error: {e}")
    dpoy_model, dpoy_features, dpoy_scaler = None, None, None
    
try:
    ppg_model, ppg_features, ppg_scaler = load_model_and_assets(
        get_latest_model_dir(base_dl_path, "ppg"), "ppg"
    )
except Exception as e:
    print(f"[WARNING] Skipping PPG model due to error: {e}")
    ppg_model, ppg_features, ppg_scaler = None, None, None
    
try:
    team_model, team_features, team_scaler = load_model_and_assets(
        get_latest_model_dir(base_dl_path, "best_team"), "best_team"
    )
except Exception as e:
    print(f"[WARNING] Skipping Team model due to error: {e}")
    team_model, team_features, team_scaler = None, None, None

@app.get("/")
def home():
    return {"message": "Welcome to the NBA Awards Prediction API"}

@app.get("/model_versions")
def get_versions():
    return {
        "MVP": get_latest_model_dir(base_dl_path, "MVP"),
        "DPOY": get_latest_model_dir(base_dl_path, "dpoy"),
        "PPG": get_latest_model_dir(base_dl_path, "ppg"),
        "TEAM": get_latest_model_dir(base_dl_path, "best_team")
    }

@app.post("/predict/mvp", response_model=PredictionResponse)
def predict_mvp(player: PlayerStats, _: str = Depends(verify_api_key)):
    try:
        input_tensor = preprocess_input(player.dict(), mvp_features, mvp_scaler)
        with torch.no_grad():
            prediction = mvp_model(input_tensor).item()
        return {"is_mvp": prediction > 0.5, "probability": round(prediction, 4)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/predict/dpoy", response_model=PredictionResponse)
def predict_dpoy(player: PlayerStats, _: str = Depends(verify_api_key)):
    try:
        input_tensor = preprocess_input(player.dict(), dpoy_features, dpoy_scaler)
        with torch.no_grad():
            prediction = dpoy_model(input_tensor).item()
        return {"is_dpoy": prediction > 0.5, "probability": round(prediction, 4)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/predict/ppg_leader", response_model=PredictionResponse)
def predict_ppg_leader(player: PlayerStats, _: str = Depends(verify_api_key)):
    try:
        input_tensor = preprocess_input(player.dict(), ppg_features, ppg_scaler)
        with torch.no_grad():
            prediction = ppg_model(input_tensor).item()
        return {"is_ppg_leader": prediction > 0.5, "probability": round(prediction, 4)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/predict/team", response_model=PredictionResponse)
def predict_team(team: TeamStats, _: str = Depends(verify_api_key)):
    try:
        input_tensor = preprocess_input(team.dict(), team_features, team_scaler)
        with torch.no_grad():
            prediction = team_model(input_tensor).item()
        return {"expected_wins": round(prediction, 2)}
    except Exception as e:
        return {"error": str(e)}


