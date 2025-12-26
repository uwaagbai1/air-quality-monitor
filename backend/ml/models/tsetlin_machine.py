import numpy as np
import joblib
import time
from typing import Dict, Any
from sklearn.metrics import accuracy_score

from ..base_model import BaseModel, get_aqi_label


class TsetlinMachine(BaseModel):
    """
    Tsetlin Machine for AQI classification using pyTsetlinMachine library.
    
    Tsetlin Machines are interpretable ML models that use propositional logic
    (AND, OR, NOT) to make decisions. Key advantages:
    - Very low energy consumption (ideal for edge/IoT)
    - Fast inference (boolean operations)
    - Interpretable rules
    - Small memory footprint
    
    This implementation uses the MultiClassTsetlinMachine from pyTsetlinMachine.
    """
    
    def __init__(self, n_clauses: int = 2000, T: int = 50, s: float = 5.0):
        """
        Initialize Tsetlin Machine.
        
        Args:
            n_clauses: Number of clauses per class (more = better accuracy, slower)
            T: Threshold for clause voting
            s: Specificity parameter (controls pattern generalization)
        """
        super().__init__()
        self.n_clauses = n_clauses
        self.T = T
        self.s = s
        
        self.model = None
        self.n_classes = 5
        self.n_features = 3
        self.n_bits = 8  # Bits per feature for booleanization
        
        # Feature scaling parameters
        self.feature_mins = None
        self.feature_maxs = None
        
        self.metadata.update({
            'name': 'Tsetlin Machine',
            'id': 'tsetlin',
            'description': 'Logic-based ML with ultra-low energy consumption',
            'complexity': 'low',
            'highlight': True,  # Research highlight
            'n_clauses': n_clauses,
            'T': T,
            's': s,
        })
    
    def _booleanize(self, X: np.ndarray) -> np.ndarray:
        """
        Convert continuous features to boolean using thermometer encoding.
        
        Each feature is converted to n_bits boolean values using thresholds.
        Example: value 0.6 with 8 bits -> [1,1,1,1,1,0,0,0]
        """
        n_samples = X.shape[0]
        
        # Normalize to 0-1 range
        X_norm = np.zeros_like(X)
        for f in range(self.n_features):
            range_val = self.feature_maxs[f] - self.feature_mins[f]
            if range_val > 0:
                X_norm[:, f] = (X[:, f] - self.feature_mins[f]) / range_val
            else:
                X_norm[:, f] = 0.5
        
        X_norm = np.clip(X_norm, 0, 1)
        
        # Thermometer encoding
        n_bool_features = self.n_features * self.n_bits
        X_bool = np.zeros((n_samples, n_bool_features), dtype=np.uint8)
        
        for f in range(self.n_features):
            for b in range(self.n_bits):
                threshold = (b + 1) / self.n_bits
                X_bool[:, f * self.n_bits + b] = (X_norm[:, f] >= threshold).astype(np.uint8)
        
        return X_bool
    
    def train(self, X_train, y_train, X_val=None, y_val=None) -> Dict[str, Any]:
        """Train the Tsetlin Machine."""
        start_time = time.time()
        
        # Learn feature ranges for normalization
        self.feature_mins = X_train.min(axis=0)
        self.feature_maxs = X_train.max(axis=0)
        
        # Booleanize features
        X_train_bool = self._booleanize(X_train)
        
        # Ensure y is integer
        y_train = y_train.astype(np.int32)
        
        # Try to use pyTsetlinMachine
        try:
            from pyTsetlinMachine.tm import MultiClassTsetlinMachine
            
            self.model = MultiClassTsetlinMachine(
                number_of_clauses=self.n_clauses,
                T=self.T,
                s=self.s,
                weighted_clauses=True
            )
            
            # Train for multiple epochs
            best_acc = 0
            for epoch in range(30):
                self.model.fit(X_train_bool, y_train, epochs=1, incremental=True)
                
                # Check validation accuracy
                if X_val is not None:
                    X_val_bool = self._booleanize(X_val)
                    val_preds = self.model.predict(X_val_bool)
                    val_acc = accuracy_score(y_val, val_preds)
                    if val_acc > best_acc:
                        best_acc = val_acc
                    # Early stopping if good enough
                    if val_acc > 0.95:
                        break
            
            self._use_library = True
            print(f"   ✅ Using pyTsetlinMachine library")
            
        except ImportError:
            print("   ⚠️ pyTsetlinMachine not installed, using fallback implementation")
            self._train_fallback(X_train_bool, y_train)
            self._use_library = False
        
        self.is_trained = True
        training_time = time.time() - start_time
        
        # Calculate accuracy
        train_preds = self._predict_batch(X_train)
        train_acc = accuracy_score(y_train, train_preds)
        
        val_acc = None
        if X_val is not None:
            val_preds = self._predict_batch(X_val)
            val_acc = accuracy_score(y_val, val_preds)
        
        # Update metadata
        self.metadata['accuracy'] = round(val_acc if val_acc else train_acc, 4)
        self.metadata['training_time_sec'] = round(training_time, 2)
        self.metadata['trained_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'train_accuracy': train_acc,
            'val_accuracy': val_acc,
            'training_time': training_time,
        }
    
    def _train_fallback(self, X_bool, y_train):
        """Fallback training if pyTsetlinMachine not available."""
        n_bool_features = X_bool.shape[1]
        
        # Initialize clause patterns and weights
        self.clause_patterns = np.random.randint(
            0, 2, size=(self.n_classes, self.n_clauses // self.n_classes, n_bool_features)
        ).astype(np.int8)
        self.clause_weights = np.zeros((self.n_classes, self.n_clauses // self.n_classes))
        
        # Simple training
        for epoch in range(20):
            for i in range(len(X_bool)):
                x = X_bool[i]
                y = y_train[i]
                
                for c in range(self.n_classes):
                    for j in range(self.n_clauses // self.n_classes):
                        pattern = self.clause_patterns[c, j]
                        clause_output = np.all(x[pattern == 1] == 1) if np.any(pattern) else False
                        
                        if c == y and clause_output:
                            self.clause_weights[c, j] += 0.1
                        elif c != y and clause_output:
                            self.clause_weights[c, j] -= 0.05
    
    def _predict_batch(self, X: np.ndarray) -> np.ndarray:
        """Predict for batch of samples."""
        X_bool = self._booleanize(X)
        
        if hasattr(self, '_use_library') and self._use_library and self.model is not None:
            return self.model.predict(X_bool)
        else:
            # Fallback prediction
            predictions = []
            for x in X_bool:
                class_scores = np.zeros(self.n_classes)
                for c in range(self.n_classes):
                    for j in range(self.clause_patterns.shape[1]):
                        pattern = self.clause_patterns[c, j]
                        if np.any(pattern):
                            clause_output = np.all(x[pattern == 1] == 1)
                            if clause_output:
                                class_scores[c] += self.clause_weights[c, j]
                predictions.append(np.argmax(class_scores))
            return np.array(predictions)
    
    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make a prediction with timing."""
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
        
        X_bool = self._booleanize(X)
        
        if hasattr(self, '_use_library') and self._use_library and self.model is not None:
            category = int(self.model.predict(X_bool)[0])
            # Get clause votes for confidence estimate
            try:
                votes = []
                for c in range(self.n_classes):
                    # Sum of clause outputs for this class
                    vote = np.sum(self.model.predict(X_bool) == c)
                    votes.append(vote)
                votes = np.array(votes, dtype=float)
                votes = votes + 1  # Smoothing
                probabilities = votes / votes.sum()
            except:
                probabilities = np.zeros(self.n_classes)
                probabilities[category] = 0.9
                probabilities = probabilities / probabilities.sum()
        else:
            # Fallback prediction
            x = X_bool[0]
            class_scores = np.zeros(self.n_classes)
            for c in range(self.n_classes):
                for j in range(self.clause_patterns.shape[1]):
                    pattern = self.clause_patterns[c, j]
                    if np.any(pattern):
                        clause_output = np.all(x[pattern == 1] == 1)
                        if clause_output:
                            class_scores[c] += self.clause_weights[c, j]
            
            category = int(np.argmax(class_scores))
            exp_scores = np.exp(class_scores - np.max(class_scores))
            probabilities = exp_scores / exp_scores.sum()
        
        confidence = float(probabilities[category])
        
        end = time.perf_counter()
        inference_time_ms = (end - start) * 1000
        
        # Update metadata - Tsetlin is very fast!
        self.metadata['avg_inference_time_ms'] = round(inference_time_ms, 3)
        self.metadata['energy_per_inference_mj'] = self._estimate_energy(
            inference_time_ms, 'low'  # Low complexity = low energy
        )
        
        return {
            'category': category,
            'label': get_aqi_label(category),
            'confidence': round(confidence, 3),
            'inference_time_ms': round(inference_time_ms, 3),
            'probabilities': {get_aqi_label(i): round(p, 3) for i, p in enumerate(probabilities)},
        }
    
    def save(self, path: str) -> bool:
        """Save model to disk."""
        try:
            save_data = {
                'feature_mins': self.feature_mins,
                'feature_maxs': self.feature_maxs,
                'n_clauses': self.n_clauses,
                'n_classes': self.n_classes,
                'n_features': self.n_features,
                'n_bits': self.n_bits,
                'T': self.T,
                's': self.s,
                'metadata': self.metadata,
                '_use_library': getattr(self, '_use_library', False),
            }
            
            if hasattr(self, '_use_library') and self._use_library and self.model is not None:
                # Save entire pyTsetlinMachine model object
                save_data['model_object'] = self.model
            else:
                # Save fallback model
                save_data['clause_patterns'] = self.clause_patterns
                save_data['clause_weights'] = self.clause_weights
            
            joblib.dump(save_data, path, compress=3)
            
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.metadata['battery_life_days'] = self._estimate_battery_life(
                self.metadata.get('energy_per_inference_mj', 0.1)
            )
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """Load model from disk."""
        try:
            data = joblib.load(path)
            
            self.feature_mins = data['feature_mins']
            self.feature_maxs = data['feature_maxs']
            self.n_clauses = data['n_clauses']
            self.n_classes = data['n_classes']
            self.n_features = data['n_features']
            self.n_bits = data.get('n_bits', 8)
            self.T = data.get('T', 50)
            self.s = data.get('s', 5.0)
            self.metadata = data['metadata']
            self._use_library = data.get('_use_library', False)
            
            if self._use_library and 'model_object' in data:
                # Load entire pyTsetlinMachine model object
                self.model = data['model_object']
            elif self._use_library and 'model_state' in data:
                # Legacy: try to load from state (may not work with all versions)
                try:
                    from pyTsetlinMachine.tm import MultiClassTsetlinMachine
                    
                    self.model = MultiClassTsetlinMachine(
                        number_of_clauses=self.n_clauses,
                        T=self.T,
                        s=self.s,
                        weighted_clauses=True
                    )
                    
                    # Initialize model with dummy data before setting state
                    n_bool_features = self.n_features * self.n_bits
                    dummy_X = np.zeros((self.n_classes, n_bool_features), dtype=np.uint8)
                    dummy_y = np.arange(self.n_classes, dtype=np.int32)
                    self.model.fit(dummy_X, dummy_y, epochs=1)
                    self.model.set_state(data['model_state'])
                    
                except Exception as e:
                    print(f"   ⚠️ Could not load TM state: {e}")
                    print("   Re-training Tsetlin Machine is recommended")
                    return False
            else:
                # Load fallback model
                self.clause_patterns = data.get('clause_patterns')
                self.clause_weights = data.get('clause_weights')
            
            self.metadata['model_size_kb'] = self._get_model_size(path)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False