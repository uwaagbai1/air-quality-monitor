"""
ML Models Package
All available models for air quality classification
"""
from .random_forest import RandomForestModel
from .tsetlin_machine import TsetlinMachine
from .decision_tree import DecisionTreeModel
from .logistic_regression import LogisticRegressionModel
from .neural_network import NeuralNetworkModel
from .xgboost_model import XGBoostModel

__all__ = [
    'RandomForestModel',
    'TsetlinMachine',
    'DecisionTreeModel',
    'LogisticRegressionModel',
    'NeuralNetworkModel',
    'XGBoostModel',
]

# Model registry for easy access
MODEL_REGISTRY = {
    'random_forest': RandomForestModel,
    'tsetlin': TsetlinMachine,
    'decision_tree': DecisionTreeModel,
    'logistic_regression': LogisticRegressionModel,
    'neural_network': NeuralNetworkModel,
    'xgboost': XGBoostModel,
}

def get_model_class(model_id: str):
    """Get model class by ID."""
    return MODEL_REGISTRY.get(model_id)

def list_models():
    """List all available model IDs."""
    return list(MODEL_REGISTRY.keys())
