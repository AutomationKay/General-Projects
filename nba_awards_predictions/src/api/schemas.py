# src/api/schemas.py

from pydantic import BaseModel, Field

class PlayerStats(BaseModel):
    PTS: float
    TRB: float
    AST: float
    STL: float
    BLK: float
    TOV: float
    FG_pct: float
    FT_pct: float
    PER: float
    WS: float

class TeamStats(BaseModel):
    FG: float
    FGA: float
    FG_pct: float
    three_p: float = Field(..., alias = "3P")
    three_pa: float = Field(..., alias = "3PA")
    three_pct: float = Field(..., alias = "3P%")
    FT: float
    FTA: float
    FT_pct: float
    ORB: float
    DRB: float
    TRB: float
    AST: float
    STL: float
    BLK: float
    TOV: float
    PF: float
    PTS: float
    Pace: float
    ORtg: float
    DRtg: float
    NetRtg: float

class PredictionResponse(BaseModel):
    prediction: str
    probability: float
