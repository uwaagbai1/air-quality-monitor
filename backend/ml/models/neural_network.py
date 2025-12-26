import numpy as np
import joblib
import time
from typing import Dict, Any
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

from ..base_model import BaseModel, get_aqi_label


class NeuralNetworkModel(BaseModel):
    # Multi-layer Perceptron classifier for AQI prediction
    
    def __init__(self, hidden_layers: tuple = (64, 32)):
        super().__init__()
        self.hidden_layers = hidden_layers
        self.model = MLPClassifier(
            hidden_layer_sizes=hidden_layers,
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        self.scaler = StandardScaler()
        self.metadata.update({
            'name': 'Neural Network',
            'id': 'neural_network',
            'description': f'MLP with layers {hidden_layers} - highest accuracy',
            'complexity': 'very_high',
        })
    
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        # Train the Neural Network model
        start_time = time.time()
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        self.model.fit(X_train_scaled, y_train)
        self.is_trained = True
        
        training_time = time.time() - start_time
        
        train_acc = accuracy_score(y_train, self.model.predict(X_train_scaled))
        val_acc = None
        if X_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            val_acc = accuracy_score(y_val, self.model.predict(X_val_scaled))
        
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
        
        X = np.array([[
            features.get('temperature', 20),
            features.get('humidity', 50),
            features.get('gas_resistance', 100000)
        ]])
        
        start = time.perf_counter()
        
        X_scaled = self.scaler.transform(X)
        category = int(self.model.predict(X_scaled)[0])
        probabilities = self.model.predict_proba(X_scaled)[0]
        confidence = float(probabilities[category])
        
        end = time.perf_counter()
        inference_time_ms = (end - start) * 1000
        
        self.metadata['avg_inference_time_ms'] = round(inference_time_ms, 3)
        self.metadata['energy_per_inference_mj'] = self._estimate_energy(
            inference_time_ms, 'very_high'
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
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'metadata': self.metadata
            }, path)
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.metadata['battery_life_days'] = self._estimate_battery_life(
                self.metadata.get('energy_per_inference_mj', 5.0)
            )
            return True
        except Exception as e:
            print(f"Error saving: {e}")
            return False
    
    def load(self, path: str) -> bool:
        try:
            data = joblib.load(path)
            self.model = data['model']
            self.scaler = data['scaler']
            self.metadata = data['metadata']
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading: {e}")
            return False
