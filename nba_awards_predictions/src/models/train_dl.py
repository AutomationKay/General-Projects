# src/models/train_ml.py

from src.utils.logger import get_logger
import pandas as pd
import joblib
import os

logger = get_logger(__name__)

def train_ml_models():
    logger.info("Training ML models started.")

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score

    # MVP Model
    logger.info("Training Most Valuable Player ML model")
    mvp_data = pd.read_csv("data/processed/mvp_eda_cleaned.csv")
    X = mvp_data.drop(columns=["is_MVP"])
    y = mvp_data["is_MVP"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    logger.info(f"MVP Model Accuracy: {acc:.4f}")
    joblib.dump(clf, "models/mvp_rf_model.pkl")

    # DPOY Model
    logger.info("Training Defensive Player of the Year ML model")
    dpoy_data = pd.read_csv("data/processed/dpoy_model_data.csv")
    X = dpoy_data.drop(columns=["is_DPOY"])
    y = dpoy_data["is_DPOY"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf_dpoy = LogisticRegression(max_iter=1000)
    clf_dpoy.fit(X_train, y_train)
    preds = clf_dpoy.predict(X_test)
    acc = accuracy_score(y_test, preds)
    logger.info(f"DPOY Model Accuracy: {acc:.4f}")
    joblib.dump(clf_dpoy, "models/dpoy_lr_model.pkl")

    logger.info("ML training complete.")
