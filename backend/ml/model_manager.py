import os
from typing import Dict, Any, Optional, List
from .models import MODEL_REGISTRY, list_models


class ModelManager:
    """
    Manages all ML models for air quality prediction.
    Supports loading, switching, and comparing models.
    """
    
    def __init__(self, models_dir: str = None):
        self.models_dir = models_dir or os.path.join(
            os.path.dirname(__file__), 'saved_models'
        )
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.models: Dict[str, Any] = {}
        self.active_model_id: str = 'random_forest'
        self.comparison_cache: Optional[List[Dict]] = None
    
    def load_all_models(self) -> Dict[str, bool]:
        """Load all available trained models."""
        results = {}
        
        for model_id in list_models():
            model_path = os.path.join(self.models_dir, f"{model_id}.pkl")
            
            if os.path.exists(model_path):
                try:
                    model_class = MODEL_REGISTRY[model_id]
                    model = model_class()
                    if model.load(model_path):
                        self.models[model_id] = model
                        results[model_id] = True
                        print(f"   ✅ Loaded {model_id}")
                    else:
                        results[model_id] = False
                except Exception as e:
                    print(f"   ❌ Failed to load {model_id}: {e}")
                    results[model_id] = False
            else:
                results[model_id] = False
        
        # Set active model to first loaded model
        if self.models:
            self.active_model_id = list(self.models.keys())[0]
        
        # Invalidate comparison cache
        self.comparison_cache = None
        
        return results
    
    def get_model(self, model_id: str = None):
        """Get a specific model or the active model."""
        model_id = model_id or self.active_model_id
        return self.models.get(model_id)
    
    def set_active_model(self, model_id: str) -> bool:
        """Set the active model for predictions."""
        if model_id in self.models:
            self.active_model_id = model_id
            return True
        return False
    
    def predict(self, features: Dict[str, float], model_id: str = None) -> Dict[str, Any]:
        """
        Make a prediction using the specified or active model.
        
        Args:
            features: Dict with temperature, humidity, gas_resistance
            model_id: Optional model ID, uses active model if not specified
            
        Returns:
            Prediction dict with category, label, confidence, timing
        """
        model = self.get_model(model_id)
        
        if model is None:
            # Fallback to rule-based if no model loaded
            return self._rule_based_predict(features)
        
        try:
            prediction = model.predict(features)
            prediction['model_used'] = model.metadata['id']
            prediction['model_name'] = model.metadata['name']
            return prediction
        except Exception as e:
            print(f"Prediction error: {e}")
            return self._rule_based_predict(features)
    
    def _rule_based_predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback rule-based prediction."""
        gas = features.get('gas_resistance', 100000)
        
        if gas > 200000:
            category = 0  # Good
        elif gas > 150000:
            category = 1  # Moderate
        elif gas > 100000:
            category = 2  # Unhealthy for Sensitive
        elif gas > 50000:
            category = 3  # Unhealthy
        else:
            category = 4  # Very Unhealthy
        
        labels = ['Good', 'Moderate', 'Unhealthy for Sensitive Groups', 
                  'Unhealthy', 'Very Unhealthy']
        
        return {
            'category': category,
            'label': labels[category],
            'confidence': 0.75,
            'inference_time_ms': 0.01,
            'model_used': 'rule_based',
            'model_name': 'Rule-Based',
        }
    
    def get_all_models_info(self) -> List[Dict[str, Any]]:
        """Get metadata for all models (loaded and unloaded)."""
        models_info = []
        
        for model_id in list_models():
            if model_id in self.models:
                # Loaded model - get live metadata
                model = self.models[model_id]
                info = model.get_metadata()
                info['loaded'] = True
                info['active'] = (model_id == self.active_model_id)
            else:
                # Not loaded - provide basic info
                model_class = MODEL_REGISTRY[model_id]
                temp_model = model_class()
                info = temp_model.get_metadata()
                info['loaded'] = False
                info['active'] = False
            
            models_info.append(info)
        
        return models_info
    
    def get_comparison(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get comparison data for all loaded models.
        Results are cached for performance.
        """
        if self.comparison_cache is not None and not force_refresh:
            return self.comparison_cache
        
        comparison = []
        
        for model_id, model in self.models.items():
            meta = model.get_metadata()
            comparison.append({
                'id': meta['id'],
                'name': meta['name'],
                'accuracy': meta.get('accuracy', 0) * 100,  # Convert to percentage
                'inference_time_ms': meta.get('avg_inference_time_ms', 0),
                'model_size_kb': meta.get('model_size_kb', 0),
                'energy_mj': meta.get('energy_per_inference_mj', 0),
                'battery_days': self._calculate_battery_days(meta.get('energy_per_inference_mj', 0)),
                'complexity': meta.get('complexity', 'medium'),
                'highlight': meta.get('highlight', False),
            })
        
        # Sort by accuracy descending
        comparison.sort(key=lambda x: x['accuracy'], reverse=True)
        
        self.comparison_cache = comparison
        return comparison
    
    def _calculate_battery_days(self, energy_mj: float) -> float:
        """Calculate battery life from energy per inference."""
        if energy_mj <= 0:
            return 0
        
        # Battery: 1000mAh @ 3.7V = 13,320,000 mJ
        battery_energy_mj = 1000 * 3.7 * 3600
        
        # Inferences per day (every 30 seconds)
        inferences_per_day = (24 * 3600) / 30
        
        # Energy per day from inference
        energy_per_day_mj = energy_mj * inferences_per_day
        
        # Add baseline (sleep mode ~0.1mW)
        baseline_per_day_mj = 0.1 * 24 * 3600
        
        total_per_day = energy_per_day_mj + baseline_per_day_mj
        
        if total_per_day > 0:
            return round(battery_energy_mj / total_per_day, 1)
        return 0

    def get_model_count(self) -> Dict[str, int]:
        """Get count of loaded vs available models."""
        return {
            'loaded': len(self.models),
            'available': len(list_models()),
        }


# Global instance
model_manager = ModelManager()
