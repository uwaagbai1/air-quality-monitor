import numpy as np
import joblib
import time
from typing import Dict, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from ..base_model import BaseModel, get_aqi_label


class RandomForestModel(BaseModel):
    # Random Forest classifier for AQI prediction
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 10):
        super().__init__()
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=42,
            n_jobs=-1
        )
        self.metadata.update({
            'name': 'Random Forest',
            'id': 'random_forest',
            'description': 'Ensemble of decision trees with bagging',
            'complexity': 'medium',
        })
    
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        # Train the Random Forest model
        start_time = time.time()
        
        # Train
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        training_time = time.time() - start_time
        
        # Calculate accuracy
        train_acc = accuracy_score(y_train, self.model.predict(X_train))
        val_acc = accuracy_score(y_val, self.model.predict(X_val)) if X_val is not None else None
        
        # Update metadata
        self.metadata['accuracy'] = round(val_acc if val_acc else train_acc, 4)
        self.metadata['training_time_sec'] = round(training_time, 2)
        self.metadata['trained_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'training_time': training_time,
        }
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        # Make a prediction with timing
        if not self.is_trained:
            raise RuntimeError("Model not trained")
        
        # Prepare features
        X = np.array([[
            features.get('temperature', 20),
            features.get('humidity', 50),
            features.get('gas_resistance', 100000)
        ]])
        
        # Time the prediction
        start = time.perf_counter()
        
        category = int(self.model.predict(X)[0])
        probabilities = self.model.predict_proba(X)[0]
        confidence = float(probabilities[category])
        
        end = time.perf_counter()
        inference_time_ms = (end - start) * 1000
        
        # Update running average of inference time
        self.metadata['avg_inference_time_ms'] = round(inference_time_ms, 3)
        self.metadata['energy_per_inference_mj'] = self._estimate_energy(
            inference_time_ms, 'medium'
        )
        
        return {
            'category': category,
            'label': get_aqi_label(category),
            'confidence': round(confidence, 3),
            'inference_time_ms': round(inference_time_ms, 3),
            'probabilities': {get_aqi_label(i): round(p, 3) for i, p in enumerate(probabilities)},
        }
    
    def save(self, path: str) -> bool:
        # Save model to disk
        try:
            joblib.dump({
                'model': self.model,
                'metadata': self.metadata,
            }, path)
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.metadata['battery_life_days'] = self._estimate_battery_life(
                self.metadata.get('energy_per_inference_mj', 1.0)
            )
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load(self, path: str) -> bool:
        # Load model from disk
        try:
            data = joblib.load(path)
            self.model = data['model']
            self.metadata = data['metadata']
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
