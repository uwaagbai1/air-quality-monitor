from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
import time
import os


class BaseModel(ABC):
    # Abstract base class for all air quality prediction models
    
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.metadata = {
            'name': 'Base Model',
            'id': 'base',
            'description': 'Abstract base model',
            'accuracy': 0.0,
            'model_size_kb': 0.0,
            'avg_inference_time_ms': 0.0,
            'energy_per_inference_mj': 0.0,
            'trained_at': None,
        }
    
    @abstractmethod
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        """
        Train the model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Dict with training metrics
        """
        pass
    
    @abstractmethod
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Make a prediction.
        
        Args:
            features: Dict with 'temperature', 'humidity', 'gas_resistance'
            
        Returns:
            Dict with 'category', 'label', 'confidence', 'inference_time_ms'
        """
        pass
    
    @abstractmethod
    def save(self, path: str) -> bool:
        """Save model to disk."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> bool:
        """Load model from disk."""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get model metadata for comparison."""
        return self.metadata.copy()
    
    def _measure_inference_time(self, predict_func, *args, n_runs: int = 100) -> float:
        """Measure average inference time in milliseconds."""
        times = []
        for _ in range(n_runs):
            start = time.perf_counter()
            predict_func(*args)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
        return sum(times) / len(times)
    
    def _get_model_size(self, path: str) -> float:
        """Get model file size in KB."""
        if os.path.exists(path):
            return os.path.getsize(path) / 1024
        return 0.0
    
    def _estimate_energy(self, inference_time_ms: float, model_complexity: str = 'medium') -> float:
        """
        Estimate energy per inference in millijoules.
        
        Based on typical ARM Cortex-M4 power consumption:
        - Idle: ~5mW
        - Active: ~50mW (simple ops) to ~200mW (complex ops)
        
        This is a simplified estimation for demonstration.
        Real measurements would require hardware power profiling.
        """
        # Power consumption estimates (mW) based on model complexity
        power_estimates = {
            'very_low': 10,    # Simple comparisons (decision tree, logistic reg)
            'low': 25,         # Tsetlin machine (boolean operations)
            'medium': 75,      # Random forest (multiple trees)
            'high': 150,       # XGBoost (gradient boosting)
            'very_high': 200,  # Neural network (matrix operations)
        }
        
        power_mw = power_estimates.get(model_complexity, 75)
        
        # Energy (mJ) = Power (mW) * Time (s)
        energy_mj = power_mw * (inference_time_ms / 1000)
        
        return round(energy_mj, 4)
    
    def _estimate_battery_life(self, energy_per_inference_mj: float, 
                                inference_interval_sec: int = 30,
                                battery_capacity_mah: int = 1000,
                                battery_voltage: float = 3.7) -> float:
        """
        Estimate battery life in days.
        
        Args:
            energy_per_inference_mj: Energy per inference in millijoules
            inference_interval_sec: Seconds between inferences
            battery_capacity_mah: Battery capacity in mAh
            battery_voltage: Battery voltage
            
        Returns:
            Estimated battery life in days
        """
        # Total battery energy in millijoules
        # E = C * V * 3600 (convert Ah to As, then to J)
        battery_energy_mj = battery_capacity_mah * battery_voltage * 3600
        
        # Inferences per day
        inferences_per_day = (24 * 3600) / inference_interval_sec
        
        # Energy per day
        energy_per_day_mj = energy_per_inference_mj * inferences_per_day
        
        # Add baseline power consumption (sleep mode ~0.1mW)
        baseline_energy_per_day_mj = 0.1 * 24 * 3600  # mW * seconds = mJ
        
        total_energy_per_day = energy_per_day_mj + baseline_energy_per_day_mj
        
        # Battery life in days
        if total_energy_per_day > 0:
            battery_life_days = battery_energy_mj / total_energy_per_day
            return round(battery_life_days, 1)
        
        return 0.0


# AQI category labels
AQI_LABELS = {
    0: 'Good',
    1: 'Moderate', 
    2: 'Unhealthy for Sensitive Groups',
    3: 'Unhealthy',
    4: 'Very Unhealthy',
}

def get_aqi_label(category: int) -> str:
    """Get AQI label from category number."""
    return AQI_LABELS.get(category, 'Unknown')
