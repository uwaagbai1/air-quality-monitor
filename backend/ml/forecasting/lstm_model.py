"""
LSTM Time-Series Forecasting Model
Predicts AQI values 6 hours into the future

Key Concepts:
- LSTM: Long Short-Term Memory - a type of RNN that can learn long-term patterns
- Sequence-to-Sequence: Input sequence of past readings → Output sequence of future predictions
- Sliding Window: Use past N readings to predict next M readings
"""
import numpy as np
import pickle
import os
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timedelta


class LSTMForecaster:
    
    def __init__(
        self,
        sequence_length: int = 288,    # Input sequence (24 hours at 5-min intervals)
        forecast_horizon: int = 72,     # Output horizon (6 hours at 5-min intervals)
        n_features: int = 4,            # temp, humidity, pressure, gas_resistance
        lstm_units: int = 64,           # LSTM hidden units
        dropout: float = 0.2,           # Dropout for regularization
    ):
        """
        Initialize LSTM Forecaster.
        
        Args:
            sequence_length: Number of past timesteps to use as input
            forecast_horizon: Number of future timesteps to predict
            n_features: Number of input features
            lstm_units: Number of LSTM hidden units
            dropout: Dropout rate for regularization
        """
        self.sequence_length = sequence_length
        self.forecast_horizon = forecast_horizon
        self.n_features = n_features
        self.lstm_units = lstm_units
        self.dropout = dropout
        
        self.model = None
        self.scaler_X = None
        self.scaler_y = None
        self.is_trained = False
        self.training_history = None
        
        self.metadata = {
            'name': 'LSTM Forecaster',
            'id': 'lstm_forecast',
            'description': 'Predicts AQI 6 hours ahead using LSTM neural network',
            'sequence_length': sequence_length,
            'forecast_horizon': forecast_horizon,
            'trained_at': None,
            'mse': None,
            'mae': None,
        }
    
    def build_model(self):
        """
        Build the LSTM model architecture.
        
        Architecture Explained:
        
        Input Shape: (batch_size, sequence_length, n_features)
        Example: (32, 288, 4) = 32 samples, 288 timesteps, 4 features
        
        LSTM Layer 1: Learns patterns, returns sequences
        LSTM Layer 2: Learns higher-level patterns, returns final state
        Dense Layer: Maps LSTM output to forecast horizon
        
        Why LSTM?
        - Regular neural networks treat inputs independently
        - LSTMs have "memory" - they can remember patterns from earlier in the sequence
        - Perfect for time-series where past values influence future values
        """
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
            from tensorflow.keras.optimizers import Adam
            
            self.model = Sequential([
                # Input layer
                Input(shape=(self.sequence_length, self.n_features)),
                
                # First LSTM layer - returns sequences for stacking
                LSTM(
                    self.lstm_units,
                    return_sequences=True,  # Output sequence for next LSTM
                    name='lstm_1'
                ),
                Dropout(self.dropout),  # Prevent overfitting
                
                # Second LSTM layer - returns final state only
                LSTM(
                    self.lstm_units // 2,  # Smaller layer
                    return_sequences=False,  # Only output final state
                    name='lstm_2'
                ),
                Dropout(self.dropout),
                
                # Dense layer to map to forecast horizon
                Dense(self.forecast_horizon, activation='linear', name='output')
            ])
            
            # Compile with Adam optimizer and MSE loss
            self.model.compile(
                optimizer=Adam(learning_rate=0.001),
                loss='mse',  # Mean Squared Error
                metrics=['mae']  # Mean Absolute Error
            )
            
            print(f"   ✅ LSTM model built: {self.model.count_params():,} parameters")
            return True
            
        except ImportError:
            print("   ❌ TensorFlow not installed. Run: pip install tensorflow")
            return False
    
    def prepare_data(
        self,
        readings: List[Dict],
        target_column: str = 'aqi'
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare data for LSTM training.
        
        Sliding Window Approach:
        
        Data: [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, ...]
        
        Window 1: Input=[r1,r2,r3,r4], Target=[r5,r6]
        Window 2: Input=[r2,r3,r4,r5], Target=[r6,r7]
        Window 3: Input=[r3,r4,r5,r6], Target=[r7,r8]
        ...
        
        This creates many training examples from one time series.
        """
        from sklearn.preprocessing import MinMaxScaler
        
        # Extract features
        features = []
        targets = []
        
        for r in readings:
            features.append([
                r.get('temperature', 20),
                r.get('humidity', 50),
                r.get('pressure', 1013),
                r.get('gas_resistance', 100000),
            ])
            targets.append(r.get(target_column, 50))
        
        features = np.array(features)
        targets = np.array(targets)
        
        # Normalize features to 0-1 range (important for neural networks!)
        self.scaler_X = MinMaxScaler()
        self.scaler_y = MinMaxScaler()
        
        features_scaled = self.scaler_X.fit_transform(features)
        targets_scaled = self.scaler_y.fit_transform(targets.reshape(-1, 1)).flatten()
        
        # Create sequences using sliding window
        X, y = [], []
        
        total_length = self.sequence_length + self.forecast_horizon
        
        for i in range(len(features_scaled) - total_length + 1):
            # Input: past sequence_length readings
            X.append(features_scaled[i:i + self.sequence_length])
            # Target: next forecast_horizon AQI values
            y.append(targets_scaled[i + self.sequence_length:i + total_length])
        
        X = np.array(X)
        y = np.array(y)
        
        print(f"   📊 Prepared {len(X)} sequences")
        print(f"      Input shape: {X.shape}")
        print(f"      Target shape: {y.shape}")
        
        return X, y
    
    def train(
        self,
        readings: List[Dict],
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train the LSTM model.
        
        Args:
            readings: List of reading dictionaries from database
            epochs: Number of training iterations over the data
            batch_size: Number of samples per gradient update
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training metrics
        """
        print(f"\n🧠 Training LSTM Forecaster...")
        print(f"   Data points: {len(readings)}")
        
        # Need enough data for sequences
        min_required = self.sequence_length + self.forecast_horizon + 10
        if len(readings) < min_required:
            return {
                'success': False,
                'error': f'Need at least {min_required} readings, have {len(readings)}'
            }
        
        # Build model if not built
        if self.model is None:
            if not self.build_model():
                return {'success': False, 'error': 'Failed to build model'}
        
        # Prepare data
        X, y = self.prepare_data(readings)
        
        # Train/validation split
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        print(f"   Training samples: {len(X_train)}")
        print(f"   Validation samples: {len(X_val)}")
        print(f"   Training for {epochs} epochs...")
        
        # Train
        try:
            from tensorflow.keras.callbacks import EarlyStopping
            
            # Early stopping to prevent overfitting
            early_stop = EarlyStopping(
                monitor='val_loss',
                patience=10,
                restore_best_weights=True
            )
            
            history = self.model.fit(
                X_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_data=(X_val, y_val),
                callbacks=[early_stop],
                verbose=1
            )
            
            self.training_history = history.history
            self.is_trained = True
            
            # Evaluate
            val_loss, val_mae = self.model.evaluate(X_val, y_val, verbose=0)
            
            # Convert MAE back to original scale
            mae_original = val_mae * (self.scaler_y.data_max_ - self.scaler_y.data_min_)
            
            self.metadata['mse'] = float(val_loss)
            self.metadata['mae'] = float(mae_original[0])
            self.metadata['trained_at'] = datetime.now().isoformat()
            
            print(f"\n   ✅ Training complete!")
            print(f"      Validation MSE: {val_loss:.4f}")
            print(f"      Validation MAE: {mae_original[0]:.1f} AQI points")
            
            return {
                'success': True,
                'epochs_run': len(history.history['loss']),
                'final_loss': float(history.history['loss'][-1]),
                'final_val_loss': float(history.history['val_loss'][-1]),
                'mae_aqi': float(mae_original[0]),
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def predict(self, recent_readings: List[Dict]) -> Dict[str, Any]:
        """
        Generate forecast from recent readings.
        
        Args:
            recent_readings: Last sequence_length readings
            
        Returns:
            Dict with forecast values and timestamps
        """
        if not self.is_trained or self.model is None:
            return {'error': 'Model not trained'}
        
        if len(recent_readings) < self.sequence_length:
            return {
                'error': f'Need {self.sequence_length} readings, have {len(recent_readings)}'
            }
        
        # Take most recent readings
        readings = recent_readings[-self.sequence_length:]
        
        # Extract and scale features
        features = np.array([
            [
                r.get('temperature', 20),
                r.get('humidity', 50),
                r.get('pressure', 1013),
                r.get('gas_resistance', 100000),
            ]
            for r in readings
        ])
        
        features_scaled = self.scaler_X.transform(features)
        
        # Reshape for LSTM: (1, sequence_length, n_features)
        X = features_scaled.reshape(1, self.sequence_length, self.n_features)
        
        # Predict
        predictions_scaled = self.model.predict(X, verbose=0)[0]
        
        # Inverse scale to get actual AQI values
        predictions = self.scaler_y.inverse_transform(
            predictions_scaled.reshape(-1, 1)
        ).flatten()
        
        # Clip to valid AQI range
        predictions = np.clip(predictions, 0, 500)
        
        # Generate timestamps (assuming 5-minute intervals)
        last_timestamp = readings[-1].get('timestamp')
        if isinstance(last_timestamp, str):
            last_timestamp = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
        else:
            last_timestamp = datetime.now()
        
        forecast_timestamps = [
            (last_timestamp + timedelta(minutes=5 * (i + 1))).isoformat()
            for i in range(self.forecast_horizon)
        ]
        
        return {
            'success': True,
            'forecast': [
                {
                    'timestamp': ts,
                    'aqi': int(round(pred)),
                    'hours_ahead': round((i + 1) * 5 / 60, 1),
                }
                for i, (ts, pred) in enumerate(zip(forecast_timestamps, predictions))
            ],
            'model': 'lstm_forecast',
            'horizon_hours': self.forecast_horizon * 5 / 60,
        }
    
    def save(self, path: str) -> bool:
        """Save model and scalers to disk."""
        try:
            # Save Keras model
            model_path = path.replace('.pkl', '_model.keras')
            self.model.save(model_path)
            
            # Save scalers and metadata
            with open(path, 'wb') as f:
                pickle.dump({
                    'scaler_X': self.scaler_X,
                    'scaler_y': self.scaler_y,
                    'metadata': self.metadata,
                    'config': {
                        'sequence_length': self.sequence_length,
                        'forecast_horizon': self.forecast_horizon,
                        'n_features': self.n_features,
                        'lstm_units': self.lstm_units,
                    }
                }, f)
            
            print(f"   💾 Saved LSTM model to {path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to save: {e}")
            return False
    
    def load(self, path: str) -> bool:
        """Load model and scalers from disk."""
        try:
            from tensorflow.keras.models import load_model
            
            # Load Keras model
            model_path = path.replace('.pkl', '_model.keras')
            self.model = load_model(model_path)
            
            # Load scalers and metadata
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.scaler_X = data['scaler_X']
                self.scaler_y = data['scaler_y']
                self.metadata = data['metadata']
                
                config = data.get('config', {})
                self.sequence_length = config.get('sequence_length', self.sequence_length)
                self.forecast_horizon = config.get('forecast_horizon', self.forecast_horizon)
            
            self.is_trained = True
            print(f"   ✅ Loaded LSTM model from {path}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to load: {e}")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get model metadata."""
        return self.metadata.copy()


# Simplified LSTM using only NumPy (no TensorFlow required)
class SimpleLSTMForecaster:
    """
    Simplified forecaster using statistical methods.
    Falls back to this if TensorFlow is not available.
    
    Uses exponential smoothing + trend analysis instead of LSTM.
    """
    
    def __init__(self, forecast_horizon: int = 72):
        self.forecast_horizon = forecast_horizon
        self.alpha = 0.3  # Smoothing factor
        self.is_trained = False
        self.last_values = None
        self.trend = None
        
        self.metadata = {
            'name': 'Simple Forecaster',
            'id': 'simple_forecast',
            'description': 'Statistical forecasting using exponential smoothing',
            'forecast_horizon': forecast_horizon,
        }
    
    def train(self, readings: List[Dict]) -> Dict[str, Any]:
        """Fit the model to historical data."""
        if len(readings) < 100:
            return {'success': False, 'error': 'Need at least 100 readings'}
        
        # Extract AQI values
        aqi_values = [r.get('aqi', 50) for r in readings]
        
        # Calculate trend (slope of last 100 values)
        recent = aqi_values[-100:]
        x = np.arange(len(recent))
        self.trend = np.polyfit(x, recent, 1)[0]  # Linear trend
        
        # Store last values for smoothing
        self.last_values = aqi_values[-20:]
        
        self.is_trained = True
        
        return {
            'success': True,
            'trend_per_step': self.trend,
        }
    
    def predict(self, recent_readings: List[Dict]) -> Dict[str, Any]:
        """Generate forecast."""
        if not self.is_trained:
            return {'error': 'Model not trained'}
        
        # Get most recent AQI
        last_aqi = recent_readings[-1].get('aqi', 50)
        
        # Generate forecast with trend and mean reversion
        mean_aqi = np.mean([r.get('aqi', 50) for r in recent_readings[-50:]])
        
        forecasts = []
        current = last_aqi
        
        for i in range(self.forecast_horizon):
            # Trend component
            current += self.trend * 0.1
            
            # Mean reversion component
            current += (mean_aqi - current) * 0.01
            
            # Add some noise
            current += np.random.normal(0, 2)
            
            forecasts.append(max(0, min(500, current)))
        
        # Generate timestamps
        last_timestamp = datetime.now()
        forecast_timestamps = [
            (last_timestamp + timedelta(minutes=5 * (i + 1))).isoformat()
            for i in range(self.forecast_horizon)
        ]
        
        return {
            'success': True,
            'forecast': [
                {
                    'timestamp': ts,
                    'aqi': int(round(pred)),
                    'hours_ahead': round((i + 1) * 5 / 60, 1),
                }
                for i, (ts, pred) in enumerate(zip(forecast_timestamps, forecasts))
            ],
            'model': 'simple_forecast',
            'horizon_hours': self.forecast_horizon * 5 / 60,
        }
    
    def save(self, path: str) -> bool:
        with open(path, 'wb') as f:
            pickle.dump({
                'alpha': self.alpha,
                'trend': self.trend,
                'last_values': self.last_values,
                'metadata': self.metadata,
            }, f)
        return True
    
    def load(self, path: str) -> bool:
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
                self.alpha = data['alpha']
                self.trend = data['trend']
                self.last_values = data['last_values']
                self.metadata = data['metadata']
                self.is_trained = True
            return True
        except:
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        return self.metadata.copy()


def get_forecaster(use_lstm: bool = True):
    """Factory function to get appropriate forecaster."""
    if use_lstm:
        try:
            import tensorflow
            return LSTMForecaster()
        except ImportError:
            print("   ⚠️ TensorFlow not available, using simple forecaster")
            return SimpleLSTMForecaster()
    return SimpleLSTMForecaster()
