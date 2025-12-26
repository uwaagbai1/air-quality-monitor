import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from .lstm_model import get_forecaster, LSTMForecaster, SimpleLSTMForecaster


class ForecastManager:
    """
    Manages forecasting models and predictions.
    
    Features:
    - Lazy loading of models
    - Caching of predictions
    - Automatic model selection (LSTM vs Simple)
    """
    
    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or os.path.join(
            os.path.dirname(__file__), '..', 'saved_models'
        )
        self.forecaster = None
        self.is_loaded = False
        
        # Cache to avoid recomputing forecasts too often
        self.forecast_cache = None
        self.cache_timestamp = None
        self.cache_duration = timedelta(minutes=5)  # Refresh every 5 mins
    
    def load_model(self) -> bool:
        # Load the forecasting model
        lstm_path = os.path.join(self.models_dir, 'lstm_forecast.pkl')
        simple_path = os.path.join(self.models_dir, 'simple_forecast.pkl')
        
        # Try LSTM first
        if os.path.exists(lstm_path):
            try:
                self.forecaster = LSTMForecaster()
                if self.forecaster.load(lstm_path):
                    self.is_loaded = True
                    print("   ✅ Loaded LSTM forecaster")
                    return True
            except Exception as e:
                print(f"   ⚠️ Failed to load LSTM: {e}")
        
        # Fall back to simple forecaster
        if os.path.exists(simple_path):
            try:
                self.forecaster = SimpleLSTMForecaster()
                if self.forecaster.load(simple_path):
                    self.is_loaded = True
                    print("   ✅ Loaded simple forecaster")
                    return True
            except Exception as e:
                print(f"   ⚠️ Failed to load simple forecaster: {e}")
        
        print("   ⚠️ No forecast model found - run training first")
        return False
    
    def get_forecast(
        self,
        recent_readings: List[Dict],
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:

        # Check cache
        if not force_refresh and self._is_cache_valid():
            return self.forecast_cache
        
        # Load model if not loaded
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        if self.forecaster is None:
            return None
        
        # Generate forecast
        try:
            forecast = self.forecaster.predict(recent_readings)
            
            if forecast.get('success'):
                # Add summary statistics
                forecast['summary'] = self._generate_summary(forecast['forecast'])
                
                # Update cache
                self.forecast_cache = forecast
                self.cache_timestamp = datetime.now()
            
            return forecast
            
        except Exception as e:
            return {'error': str(e)}
    
    def _is_cache_valid(self) -> bool:
        # Check if cached forecast is still valid
        if self.forecast_cache is None or self.cache_timestamp is None:
            return False
        
        age = datetime.now() - self.cache_timestamp
        return age < self.cache_duration
    
    def _generate_summary(self, forecast: List[Dict]) -> Dict[str, Any]:
        # Generate summary statistics for forecast
        aqi_values = [f['aqi'] for f in forecast]
        
        # Find peaks and valleys
        max_aqi = max(aqi_values)
        min_aqi = min(aqi_values)
        max_idx = aqi_values.index(max_aqi)
        min_idx = aqi_values.index(min_aqi)
        
        # Calculate trend
        first_half = sum(aqi_values[:len(aqi_values)//2]) / (len(aqi_values)//2)
        second_half = sum(aqi_values[len(aqi_values)//2:]) / (len(aqi_values)//2)
        
        if second_half > first_half * 1.1:
            trend = 'worsening'
        elif second_half < first_half * 0.9:
            trend = 'improving'
        else:
            trend = 'stable'
        
        # Generate alert if needed
        alert = None
        if max_aqi > 150:
            alert = {
                'type': 'aqi_forecast',
                'severity': 'warning' if max_aqi < 200 else 'critical',
                'message': f'AQI expected to reach {max_aqi} in {forecast[max_idx]["hours_ahead"]}h',
                'timestamp': forecast[max_idx]['timestamp'],
            }
        
        return {
            'avg_aqi': round(sum(aqi_values) / len(aqi_values)),
            'max_aqi': max_aqi,
            'min_aqi': min_aqi,
            'max_at_hours': forecast[max_idx]['hours_ahead'],
            'min_at_hours': forecast[min_idx]['hours_ahead'],
            'trend': trend,
            'alert': alert,
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        # Get information about the loaded model
        if self.forecaster is None:
            return {
                'loaded': False,
                'name': 'Not loaded',
            }
        
        metadata = self.forecaster.get_metadata()
        return {
            'loaded': self.is_loaded,
            'name': metadata.get('name', 'Unknown'),
            'id': metadata.get('id', 'unknown'),
            'forecast_horizon': metadata.get('forecast_horizon', 0),
            'mae': metadata.get('mae', None),
            'trained_at': metadata.get('trained_at', None),
        }
    
    def invalidate_cache(self):
        # Clear the forecast cache
        self.forecast_cache = None
        self.cache_timestamp = None


# Global instance
forecast_manager = ForecastManager()
