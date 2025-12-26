"""
Forecasting Module
LSTM and statistical forecasting for air quality predictions
"""
from .lstm_model import LSTMForecaster, SimpleLSTMForecaster, get_forecaster
from .forecast_manager import ForecastManager, forecast_manager

__all__ = [
    'LSTMForecaster',
    'SimpleLSTMForecaster', 
    'get_forecaster',
    'ForecastManager',
    'forecast_manager',
]
