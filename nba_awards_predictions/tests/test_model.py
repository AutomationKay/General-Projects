# tests/test_model.py
import pytest
from src.models.train_model import train_model, evaluate_model
from sklearn.datasets import make_classification

@pytest.fixture
def sample_data():
    X, y = make_classification(n_samples=100, n_features=5, random_state=42)
    return X, y

def test_train_model(sample_data):
    X, y = sample_data
    model = train_model(X, y)
    assert model is not None, "Model should not be None"
    assert hasattr(model, "predict"), "Model should have a predict method"

def test_evaluate_model(sample_data):
    X, y = sample_data
    model = train_model(X, y)
    accuracy = evaluate_model(model, X, y)
    assert 0 <= accuracy <= 1, "Accuracy must be between 0 and 1"
