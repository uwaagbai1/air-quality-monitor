import os
import sys
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.models import MODEL_REGISTRY, list_models


def load_and_prepare_data(data_path: str):
    """
    Load UCI Air Quality dataset and prepare features/labels.
    
    The UCI dataset has these relevant columns:
    - T: Temperature
    - RH: Relative Humidity  
    - PT08.S1-S5: Metal oxide sensor responses (similar to BME680 gas)
    - CO(GT), C6H6(GT), NOx(GT), NO2(GT): Ground truth pollutant levels
    
    We'll create AQI categories based on pollutant levels.
    """
    print(f"📂 Loading data from {data_path}...")
    
    # Try different separators and encodings
    try:
        df = pd.read_csv(data_path, sep=';', decimal=',', encoding='utf-8')
    except:
        try:
            df = pd.read_csv(data_path, sep=',', encoding='utf-8')
        except:
            df = pd.read_csv(data_path, sep=';', decimal=',', encoding='latin-1')
    
    print(f"   Loaded {len(df)} rows")
    print(f"   Columns: {list(df.columns)}")
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Handle missing values (marked as -200 in this dataset)
    df = df.replace(-200, np.nan)
    
    # Select relevant columns
    # Map UCI columns to our feature names
    feature_mapping = {
        'T': 'temperature',
        'RH': 'humidity',
        'PT08.S1(CO)': 'gas_resistance',  # Metal oxide sensor as proxy
    }
    
    # Check which columns exist
    available_cols = []
    for uci_col, our_col in feature_mapping.items():
        if uci_col in df.columns:
            available_cols.append(uci_col)
        else:
            # Try variations
            for col in df.columns:
                if uci_col.lower() in col.lower():
                    feature_mapping[col] = our_col
                    available_cols.append(col)
                    break
    
    print(f"   Using columns: {available_cols}")
    
    # If we don't have the right columns, create synthetic data
    if len(available_cols) < 3:
        print("   ⚠️ Creating synthetic training data...")
        return create_synthetic_data()
    
    # Rename columns
    df_features = df[available_cols].copy()
    df_features.columns = [feature_mapping.get(c, c) for c in available_cols]
    
    # Drop rows with missing values
    df_features = df_features.dropna()
    print(f"   After cleaning: {len(df_features)} rows")
    
    # Create AQI categories based on gas sensor readings
    # Higher sensor values = more pollution = higher AQI category
    # BME680 gas resistance: higher = cleaner air (opposite!)
    # UCI PT08.Sx sensors: higher = more pollution
    
    # So we need to INVERT if using PT08 data
    gas_col = 'gas_resistance'
    if gas_col in df_features.columns:
        gas_values = df_features[gas_col].values
        
        # Check if this is PT08 style (higher = worse) or BME680 style (higher = better)
        # PT08 typically ranges 600-2000, BME680 ranges 10000-500000
        if gas_values.mean() < 10000:
            # PT08 style - convert to BME680-like scale and invert
            gas_values = 300000 - (gas_values * 100)  # Rough conversion
            df_features[gas_col] = np.clip(gas_values, 10000, 500000)
    
    # Create AQI categories based on gas resistance
    def get_aqi_category(gas):
        if gas > 200000:
            return 0  # Good
        elif gas > 150000:
            return 1  # Moderate
        elif gas > 100000:
            return 2  # Unhealthy for Sensitive
        elif gas > 50000:
            return 3  # Unhealthy
        else:
            return 4  # Very Unhealthy
    
    df_features['aqi_category'] = df_features['gas_resistance'].apply(get_aqi_category)
    
    # Prepare X and y
    X = df_features[['temperature', 'humidity', 'gas_resistance']].values
    y = df_features['aqi_category'].values
    
    print(f"\n📊 Data summary:")
    print(f"   Samples: {len(X)}")
    print(f"   Features: temperature, humidity, gas_resistance")
    print(f"   Category distribution:")
    unique, counts = np.unique(y, return_counts=True)
    labels = ['Good', 'Moderate', 'Unhealthy-Sensitive', 'Unhealthy', 'Very Unhealthy']
    for cat, count in zip(unique, counts):
        print(f"      {labels[cat]}: {count} ({count/len(y)*100:.1f}%)")
    
    return X, y


def create_synthetic_data(n_samples: int = 10000):
    """Create synthetic training data if real data not available."""
    print("   Generating synthetic training data...")
    
    np.random.seed(42)
    
    X = []
    y = []
    
    # Generate samples for each category
    samples_per_category = n_samples // 5
    
    # Category 0: Good (high gas resistance)
    for _ in range(samples_per_category):
        temp = np.random.uniform(18, 28)
        humidity = np.random.uniform(30, 60)
        gas = np.random.uniform(200000, 400000)
        X.append([temp, humidity, gas])
        y.append(0)
    
    # Category 1: Moderate
    for _ in range(samples_per_category):
        temp = np.random.uniform(18, 30)
        humidity = np.random.uniform(35, 65)
        gas = np.random.uniform(150000, 200000)
        X.append([temp, humidity, gas])
        y.append(1)
    
    # Category 2: Unhealthy for Sensitive
    for _ in range(samples_per_category):
        temp = np.random.uniform(15, 32)
        humidity = np.random.uniform(40, 70)
        gas = np.random.uniform(100000, 150000)
        X.append([temp, humidity, gas])
        y.append(2)
    
    # Category 3: Unhealthy
    for _ in range(samples_per_category):
        temp = np.random.uniform(15, 35)
        humidity = np.random.uniform(45, 75)
        gas = np.random.uniform(50000, 100000)
        X.append([temp, humidity, gas])
        y.append(3)
    
    # Category 4: Very Unhealthy
    for _ in range(samples_per_category):
        temp = np.random.uniform(10, 38)
        humidity = np.random.uniform(50, 80)
        gas = np.random.uniform(10000, 50000)
        X.append([temp, humidity, gas])
        y.append(4)
    
    X = np.array(X)
    y = np.array(y)
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    print(f"   Generated {len(X)} samples")
    
    return X, y


def train_all_models(X_train, X_val, y_train, y_val, save_dir: str):
    """Train all models and save them."""
    os.makedirs(save_dir, exist_ok=True)
    
    results = {}
    
    for model_id in list_models():
        print(f"\n{'='*50}")
        print(f"Training: {model_id}")
        print('='*50)
        
        try:
            # Create model
            model_class = MODEL_REGISTRY[model_id]
            model = model_class()
            
            # Train
            start = time.time()
            train_result = model.train(X_train, y_train, X_val, y_val)
            train_time = time.time() - start
            
            print(f"   Train accuracy: {train_result['train_accuracy']:.4f}")
            if train_result['val_accuracy']:
                print(f"   Val accuracy:   {train_result['val_accuracy']:.4f}")
            print(f"   Training time:  {train_time:.2f}s")
            
            # Test inference time
            test_features = {
                'temperature': 22.0,
                'humidity': 50.0,
                'gas_resistance': 150000
            }
            
            # Warm up
            for _ in range(10):
                model.predict(test_features)
            
            # Measure
            times = []
            for _ in range(100):
                pred = model.predict(test_features)
                times.append(pred['inference_time_ms'])
            
            avg_inference = np.mean(times)
            print(f"   Avg inference:  {avg_inference:.3f}ms")
            
            # Save
            save_path = os.path.join(save_dir, f"{model_id}.pkl")
            model.save(save_path)
            
            # Get final metadata
            metadata = model.get_metadata()
            print(f"   Model size:     {metadata['model_size_kb']:.1f} KB")
            print(f"   Energy/infer:   {metadata['energy_per_inference_mj']:.4f} mJ")
            print(f"   Battery life:   {metadata['battery_life_days']:.1f} days")
            
            results[model_id] = {
                'success': True,
                'accuracy': metadata['accuracy'],
                'inference_ms': avg_inference,
                'size_kb': metadata['model_size_kb'],
                'energy_mj': metadata['energy_per_inference_mj'],
                'battery_days': metadata['battery_life_days'],
            }
            
            print(f"   ✅ Saved to {save_path}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            results[model_id] = {'success': False, 'error': str(e)}
    
    return results


def print_comparison_table(results: dict):
    """Print a comparison table of all models."""
    print("\n")
    print("=" * 80)
    print("MODEL COMPARISON RESULTS")
    print("=" * 80)
    
    # Header
    print(f"{'Model':<20} {'Accuracy':>10} {'Inference':>12} {'Size':>10} {'Energy':>10} {'Battery':>10}")
    print(f"{'':20} {'':>10} {'(ms)':>12} {'(KB)':>10} {'(mJ)':>10} {'(days)':>10}")
    print("-" * 80)
    
    # Sort by accuracy
    sorted_results = sorted(
        [(k, v) for k, v in results.items() if v.get('success')],
        key=lambda x: x[1]['accuracy'],
        reverse=True
    )
    
    for model_id, data in sorted_results:
        name = model_id.replace('_', ' ').title()
        if model_id == 'tsetlin':
            name = 'Tsetlin Machine ⚡'
        
        print(f"{name:<20} {data['accuracy']*100:>9.1f}% {data['inference_ms']:>11.3f} "
              f"{data['size_kb']:>9.1f} {data['energy_mj']:>9.4f} {data['battery_days']:>9.1f}")
    
    print("-" * 80)
    print("\n⚡ = Energy-efficient (best for edge deployment)")
    print("\nBattery estimates: 1000mAh @ 3.7V, inference every 30 seconds")


def main():
    print("\n" + "=" * 60)
    print("  🤖 Air Quality Monitor - Model Training")
    print("=" * 60 + "\n")
    
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)
    data_path = os.path.join(backend_dir, 'data', 'AirQualityUCI.csv')
    save_dir = os.path.join(script_dir, 'saved_models')
    
    # Check for data file
    if not os.path.exists(data_path):
        print(f"⚠️ Dataset not found at {data_path}")
        print("   Using synthetic data for training...")
        X, y = create_synthetic_data()
    else:
        X, y = load_and_prepare_data(data_path)
    
    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n📊 Train/Val split:")
    print(f"   Training samples: {len(X_train)}")
    print(f"   Validation samples: {len(X_val)}")
    
    # Train all models
    results = train_all_models(X_train, X_val, y_train, y_val, save_dir)
    
    # Print comparison
    print_comparison_table(results)
    
    print("\n✅ Training complete!")
    print(f"   Models saved to: {save_dir}")


if __name__ == '__main__':
    main()
