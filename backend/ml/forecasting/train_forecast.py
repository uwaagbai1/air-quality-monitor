import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timedelta
from database import get_db, init_db
from ml.forecasting.lstm_model import LSTMForecaster, get_forecaster


def load_readings_from_db(hours: int = 168) -> list:
    """Load readings from database for training."""
    since = datetime.now() - timedelta(hours=hours)
    
    with get_db() as db:
        rows = db.execute('''
            SELECT timestamp, temperature, humidity, pressure, gas_resistance, aqi
            FROM readings
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        ''', (since.isoformat(),)).fetchall()
    
    return [dict(row) for row in rows]


def generate_synthetic_data(n_samples: int = 5000) -> list:
    """
    Generate synthetic training data if database is empty.
    Creates realistic-looking air quality patterns.
    """
    import numpy as np
    
    print("   📊 Generating synthetic training data...")
    
    readings = []
    base_time = datetime.now() - timedelta(hours=n_samples * 5 / 60)
    
    # Base values
    base_temp = 22
    base_humidity = 50
    base_pressure = 1013
    base_gas = 150000
    
    for i in range(n_samples):
        # Time of day effects (24-hour cycle)
        hour_angle = 2 * np.pi * (i % 288) / 288
        
        # Temperature: cooler at night, warmer during day
        temp = base_temp + 5 * np.sin(hour_angle - np.pi/2) + np.random.normal(0, 1)
        
        # Humidity: inverse of temperature roughly
        humidity = base_humidity - 10 * np.sin(hour_angle - np.pi/2) + np.random.normal(0, 3)
        humidity = np.clip(humidity, 20, 80)
        
        # Pressure: slow random walk
        base_pressure += np.random.normal(0, 0.1)
        base_pressure = np.clip(base_pressure, 990, 1030)
        pressure = base_pressure + np.random.normal(0, 0.5)
        
        # Gas resistance: affected by time of day (pollution patterns)
        # Lower during rush hours (higher AQI), higher at night (lower AQI)
        rush_hour_effect = -30000 * (
            np.exp(-((i % 288 - 96) ** 2) / 500) +  # Morning rush ~8am
            np.exp(-((i % 288 - 216) ** 2) / 500)   # Evening rush ~6pm
        )
        gas = base_gas + rush_hour_effect + np.random.normal(0, 10000)
        gas = max(10000, gas)
        
        # Calculate AQI from gas resistance
        if gas > 300000:
            aqi = int(np.interp(gas, [300000, 500000], [25, 0]))
        elif gas > 200000:
            aqi = int(np.interp(gas, [200000, 300000], [50, 25]))
        elif gas > 100000:
            aqi = int(np.interp(gas, [100000, 200000], [100, 50]))
        elif gas > 50000:
            aqi = int(np.interp(gas, [50000, 100000], [200, 100]))
        else:
            aqi = int(np.interp(gas, [10000, 50000], [500, 200]))
        
        aqi = np.clip(aqi, 0, 500)
        
        readings.append({
            'timestamp': (base_time + timedelta(minutes=5 * i)).isoformat(),
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'gas_resistance': round(gas, 0),
            'aqi': int(aqi),
        })
    
    print(f"   Generated {len(readings)} synthetic readings")
    print(f"   Time span: {readings[0]['timestamp']} to {readings[-1]['timestamp']}")
    print(f"   AQI range: {min(r['aqi'] for r in readings)} - {max(r['aqi'] for r in readings)}")
    
    return readings


def main():
    print("\n" + "=" * 60)
    print("   🔮 LSTM Forecasting Model Training")
    print("=" * 60 + "\n")
    
    # Initialize database
    init_db()
    
    # Load data
    print("📂 Loading training data...")
    readings = load_readings_from_db(hours=168)  # Last week
    
    if len(readings) < 500:
        print(f"   ⚠️ Only {len(readings)} readings in database")
        print("   Using synthetic data for training demo")
        readings = generate_synthetic_data(5000)
    else:
        print(f"   ✅ Loaded {len(readings)} readings")
    
    # Get appropriate forecaster
    print("\n🧠 Initializing forecaster...")
    forecaster = get_forecaster(use_lstm=True)
    print(f"   Using: {forecaster.metadata['name']}")
    
    # Train
    if isinstance(forecaster, LSTMForecaster):
        print(" Training with LSTM-specific parameters...")
        result = forecaster.train(readings, epochs=30, batch_size=32)
    else:
        # Simple forecaster doesn't use epochs or batch_size
        print(" Training simple statistical forecaster (no epochs/batch needed)...")
        result = forecaster.train(readings)
    
    if result.get('success'):
        # Save model
        models_dir = os.path.join(os.path.dirname(__file__), '..', 'saved_models')
        os.makedirs(models_dir, exist_ok=True)
       
        model_path = os.path.join(models_dir, f"{forecaster.metadata['id']}.pkl")
        forecaster.save(model_path)
       
        print("\n" + "=" * 60)
        print(" ✅ Training Complete!")
        print("=" * 60)
        print(f" Model: {forecaster.metadata['name']}")
       
        # Safely handle MAE display
        mae_value = result.get('mae_aqi')
        if mae_value is not None and isinstance(mae_value, (int, float)):
            print(f" MAE: {mae_value:.1f} AQI points")
        else:
            print(" MAE: Not available (simple forecaster)")
       
        print(f" Epochs: {result.get('epochs_run', 'N/A')}")
        print(f" Saved to: {model_path}")
        
        # Test prediction
        print("\n📊 Testing prediction...")
        test_result = forecaster.predict(readings[-forecaster.sequence_length:])
        
        if test_result.get('success'):
            forecast = test_result['forecast']
            print(f"   Forecast generated: {len(forecast)} points")
            print(f"   Time range: 0 to {forecast[-1]['hours_ahead']} hours")
            print(f"   AQI range: {min(f['aqi'] for f in forecast)} - {max(f['aqi'] for f in forecast)}")
            
            # Show sample predictions
            print("\n   Sample predictions:")
            for i in [0, 11, 23, 35, 47, 59, 71]:
                if i < len(forecast):
                    f = forecast[i]
                    print(f"      +{f['hours_ahead']:4.1f}h: AQI {f['aqi']:3d}")
    else:
        print(f"\n   ❌ Training failed: {result.get('error')}")
    
    print()


if __name__ == '__main__':
    main()
