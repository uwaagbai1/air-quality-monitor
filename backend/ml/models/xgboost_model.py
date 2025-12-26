import numpy as np
import joblib
import time
from typing import Dict, Any
from sklearn.metrics import accuracy_score

from ..base_model import BaseModel, get_aqi_label

# Try to import xgboost, fall back to sklearn
try:
    import xgboost as xgb
    USE_XGBOOST = True
except ImportError:
    from sklearn.ensemble import GradientBoostingClassifier
    USE_XGBOOST = False


class XGBoostModel(BaseModel):
    """XGBoost/Gradient Boosting classifier for AQI prediction."""
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 6):
        super().__init__()
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        
        if USE_XGBOOST:
            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                use_label_encoder=False,
                eval_metric='mlogloss'
            )
            name = 'XGBoost'
        else:
            self.model = GradientBoostingClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42
            )
            name = 'Gradient Boosting'
        
        self.metadata.update({
            'name': name,
            'id': 'xgboost',
            'description': 'Gradient boosting ensemble - high accuracy',
            'complexity': 'high',
        })
    
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        """Train the XGBoost model."""
        start_time = time.time()
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        training_time = time.time() - start_time
        
        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        val_acc = accuracy_score(y_val, self.model.predict(X_val)) if X_val is not None else None
        
        self.metadata['accuracy'] = round(val_acc if val_acc else train_acc, 4)
        self.metadata['training_time_sec'] = round(training_time, 2)
        self.metadata['trained_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'training_time': training_time,
        }
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make a prediction with timing."""
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        X = np.array([[
            features.get('temperature', 20),
            features.get('humidity', 50),
            features.get('gas_resistance', 100000)
        ]])
        
        start = time.perf_counter()
        
        category = int(self.model.predict(X)[0])
        probabilities = self.model.predict_proba(X)[0]
        confidence = float(probabilities[category])
        
        end = time.perf_counter()
        inference_time_ms = (end - start) * 1000
        
        self.metadata['avg_inference_time_ms'] = round(inference_time_ms, 3)
        self.metadata['energy_per_inference_mj'] = self._estimate_energy(
            inference_time_ms, 'high'
        )
        
        return {
            'category': category,
            'label': get_aqi_label(category),
            'confidence': round(confidence, 3),
            'inference_time_ms': round(inference_time_ms, 3),
            'probabilities': {get_aqi_label(i): round(p, 3) for i, p in enumerate(probabilities)},
        }
    
    def save(self, path: str) -> bool:
        try:
            joblib.dump({'model': self.model, 'metadata': self.metadata}, path)
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.metadata['battery_life_days'] = self._estimate_battery_life(
                self.metadata.get('energy_per_inference_mj', 2.0)
            )
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def load(self, path: str) -> bool:
        try:
            data = joblib.load(path)
            self.model = data['model']
            self.metadata = data['metadata']
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading: {e}")
            return False
