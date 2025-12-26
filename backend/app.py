import os
import sys
import json
import argparse
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS

# Local imports
from config import HOST, PORT, CORS_ORIGINS, SERIAL_PORT, SERIAL_BAUD
from database import (
    init_db, save_reading, get_latest_reading, 
    get_readings, get_readings_for_chart, get_stats,
    get_active_alerts
)
from simulator import simulator, get_aqi_category

# ML imports
from ml import model_manager
from ml.forecasting import forecast_manager

# Alert system
from alerts import alert_manager

# ============ FLASK APP SETUP ============
app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

# Global state
latest_reading: Optional[Dict[str, Any]] = None
demo_mode = False


# ============ READING PROCESSOR ============
def process_reading(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a reading: add predictions, save to DB, cache."""
    global latest_reading
    
    # Get AQI category info (rule-based fallback)
    aqi_info = get_aqi_category(data.get('aqi', 0))
    
    # Try ML prediction if models are loaded
    features = {
        'temperature': data.get('temperature', 20),
        'humidity': data.get('humidity', 50),
        'gas_resistance': data.get('gas_resistance', 100000),
    }
    
    try:
        prediction = model_manager.predict(features)
        data['prediction'] = {
            'category': prediction['category'],
            'label': prediction['label'],
            'confidence': prediction['confidence'],
        }
        data['model_used'] = prediction.get('model_used', 'rule_based')
        data['inference_time_ms'] = prediction.get('inference_time_ms', 0.1)
    except Exception as e:
        # Fallback to rule-based
        data['prediction'] = {
            'category': aqi_info['category'],
            'label': aqi_info['label'],
            'confidence': 0.85,
        }
        data['model_used'] = 'rule_based'
        data['inference_time_ms'] = 0.1
    
    # Add display info
    data['color'] = aqi_info['color']
    data['text_color'] = aqi_info['text_color']
    data['recommendation'] = aqi_info['recommendation']
    
    # Ensure timestamp
    if 'timestamp' not in data:
        data['timestamp'] = datetime.now().isoformat()
    
    # Save to database
    reading_id = save_reading(data)
    data['id'] = reading_id
    
    # Cache as latest
    latest_reading = data
    
    # Process alerts
    try:
        new_alerts = alert_manager.process_reading(data)
        if new_alerts:
            for alert in new_alerts:
                print(f"   🚨 Alert: {alert.title}")
    except Exception as e:
        print(f"   ⚠️ Alert processing error: {e}")
    
    # Log to console
    print(f"   📊 T={data['temperature']:.1f}°C | "
          f"H={data['humidity']:.1f}% | "
          f"AQI={data['aqi']} → {data['prediction']['label']} "
          f"[{data['model_used']}]")
    
    return data


# ============ SERIAL READER (for real hardware) ============
def serial_reader_thread():
    """Background thread to read from Arduino via serial."""
    import serial
    import serial.tools.list_ports
    
    ser = None
    port = SERIAL_PORT
    
    print("🔌 Serial reader starting...")
    
    while True:
        # Connect if needed
        if ser is None or not ser.is_open:
            # Auto-detect Arduino
            if not os.path.exists(port):
                ports = serial.tools.list_ports.comports()
                for p in ports:
                    if 'CH340' in p.description or 'Arduino' in p.description or 'USB' in p.description:
                        port = p.device
                        break
                else:
                    print("   ⚠️ No Arduino found. Retrying in 5s...")
                    time.sleep(5)
                    continue
            
            try:
                ser = serial.Serial(port, SERIAL_BAUD, timeout=1)
                print(f"   ✅ Connected to Arduino on {port}")
                time.sleep(2)  # Wait for Arduino reset
            except Exception as e:
                print(f"   ❌ Serial error: {e}")
                time.sleep(5)
                continue
        
        # Read data
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line and line.startswith('{'):
                    try:
                        data = json.loads(line)
                        if data.get('type') == 'reading':
                            process_reading(data)
                    except json.JSONDecodeError:
                        pass
            else:
                time.sleep(0.1)
        except Exception as e:
            print(f"   ❌ Read error: {e}")
            ser = None
            time.sleep(2)


# ============ API ROUTES ============

@app.route('/api/health')
def api_health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'mode': 'demo' if demo_mode else 'live',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
    })


@app.route('/api/latest')
def api_latest():
    """Get latest sensor reading."""
    if latest_reading:
        return jsonify(latest_reading)
    
    # Try database if no cached reading
    db_reading = get_latest_reading()
    if db_reading:
        return jsonify(db_reading)
    
    return jsonify({'error': 'No readings available'}), 404


@app.route('/api/readings')
def api_readings():
    """Get historical readings."""
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 500, type=int)
    
    readings = get_readings(hours=hours, limit=limit)
    return jsonify({
        'count': len(readings),
        'hours': hours,
        'readings': readings,
    })


@app.route('/api/chart')
def api_chart():
    """Get data formatted for charts."""
    hours = request.args.get('hours', 24, type=int)
    data = get_readings_for_chart(hours=hours)
    return jsonify(data)


@app.route('/api/stats')
def api_stats():
    """Get aggregated statistics."""
    hours = request.args.get('hours', 24, type=int)
    stats = get_stats(hours=hours)
    return jsonify(stats)


@app.route('/api/models')
def api_models():
    """List available ML models."""
    models_info = model_manager.get_all_models_info()
    model_count = model_manager.get_model_count()
    
    return jsonify({
        'models': models_info,
        'current': model_manager.active_model_id,
        'loaded': model_count['loaded'],
        'available': model_count['available'],
    })


@app.route('/api/models/compare')
def api_models_compare():
    """Get comparison data for all loaded models."""
    comparison = model_manager.get_comparison()
    
    return jsonify({
        'comparison': comparison,
        'count': len(comparison),
    })


@app.route('/api/models/set', methods=['POST'])
def api_models_set():
    """Set the active model."""
    data = request.get_json() or {}
    model_id = data.get('model_id') or request.args.get('model')
    
    if not model_id:
        return jsonify({'error': 'model_id required'}), 400
    
    success = model_manager.set_active_model(model_id)
    
    if success:
        return jsonify({
            'success': True,
            'active_model': model_id,
        })
    else:
        return jsonify({
            'error': f'Model {model_id} not loaded',
            'available': list(model_manager.models.keys()),
        }), 404


@app.route('/api/predict')
def api_predict():
    """Get prediction for current reading with specific model."""
    model_id = request.args.get('model')
    
    if not latest_reading:
        return jsonify({'error': 'No readings available'}), 404
    
    features = {
        'temperature': latest_reading.get('temperature', 20),
        'humidity': latest_reading.get('humidity', 50),
        'gas_resistance': latest_reading.get('gas_resistance', 100000),
    }
    
    try:
        prediction = model_manager.predict(features, model_id)
        
        model = model_manager.get_model(model_id)
        if model:
            metadata = model.get_metadata()
            prediction['model_accuracy'] = metadata.get('accuracy', 0)
            prediction['model_size_kb'] = metadata.get('model_size_kb', 0)
            prediction['energy_mj'] = metadata.get('energy_per_inference_mj', 0)
            prediction['battery_days'] = metadata.get('battery_life_days', 0)
        
        return jsonify(prediction)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/predict/all')
def api_predict_all():
    """Get predictions from all loaded models for comparison."""
    if not latest_reading:
        return jsonify({'error': 'No readings available'}), 404
    
    features = {
        'temperature': latest_reading.get('temperature', 20),
        'humidity': latest_reading.get('humidity', 50),
        'gas_resistance': latest_reading.get('gas_resistance', 100000),
    }
    
    predictions = {}
    
    for model_id in model_manager.models.keys():
        try:
            pred = model_manager.predict(features, model_id)
            predictions[model_id] = pred
        except Exception as e:
            predictions[model_id] = {'error': str(e)}
    
    return jsonify({
        'features': features,
        'predictions': predictions,
    })

@app.route('/api/forecast')
def api_forecast():
    """
    Get AQI forecast for the next 6 hours.
    
    Returns predicted AQI values at 5-minute intervals.
    """
    # Get recent readings for forecasting
    readings = get_readings(hours=24, limit=500)
    
    if len(readings) < 50:
        return jsonify({
            'error': 'Not enough historical data for forecasting',
            'required': 50,
            'available': len(readings),
        }), 400
    
    # Get forecast
    forecast = forecast_manager.get_forecast(readings)
    
    if forecast is None:
        return jsonify({
            'error': 'Forecast model not loaded',
            'hint': 'Run: python -m ml.forecasting.train_forecast',
        }), 503
    
    if 'error' in forecast:
        return jsonify(forecast), 500
    
    return jsonify(forecast)


@app.route('/api/forecast/summary')
def api_forecast_summary():
    """Get summarized forecast (hourly averages)."""
    readings = get_readings(hours=24, limit=500)
    
    if len(readings) < 50:
        return jsonify({'error': 'Not enough data'}), 400
    
    forecast = forecast_manager.get_forecast(readings)
    
    if forecast is None or 'error' in forecast:
        return jsonify({'error': 'Forecast not available'}), 503
    
    # Aggregate to hourly
    hourly = []
    forecast_data = forecast.get('forecast', [])
    
    for hour in range(6):
        # Get predictions for this hour (12 points per hour at 5-min intervals)
        start_idx = hour * 12
        end_idx = start_idx + 12
        hour_data = forecast_data[start_idx:end_idx]
        
        if hour_data:
            avg_aqi = sum(f['aqi'] for f in hour_data) / len(hour_data)
            hourly.append({
                'hour': hour + 1,
                'avg_aqi': round(avg_aqi),
                'min_aqi': min(f['aqi'] for f in hour_data),
                'max_aqi': max(f['aqi'] for f in hour_data),
            })
    
    return jsonify({
        'hourly': hourly,
        'summary': forecast.get('summary', {}),
        'model': forecast.get('model', 'unknown'),
    })


@app.route('/api/forecast/model')
def api_forecast_model():
    """Get information about the forecast model."""
    info = forecast_manager.get_model_info()
    return jsonify(info)

@app.route('/api/alerts')
def api_alerts():
    """Get all active alerts."""
    include_ack = request.args.get('include_acknowledged', 'false').lower() == 'true'
    alerts = alert_manager.get_all_alerts(include_acknowledged=include_ack)
    counts = alert_manager.get_alert_counts()
    
    return jsonify({
        'alerts': alerts,
        'counts': counts,
    })


@app.route('/api/alerts/active')
def api_alerts_active():
    """Get only unacknowledged alerts."""
    alerts = alert_manager.get_active_alerts()
    counts = alert_manager.get_alert_counts()
    
    return jsonify({
        'alerts': alerts,
        'counts': counts,
    })

@app.route('/api/alerts/counts')
def api_alerts_counts():
    """Get alert counts by severity."""
    counts = alert_manager.get_alert_counts()
    return jsonify(counts)


@app.route('/api/alerts/<alert_id>/acknowledge', methods=['POST'])
def api_alert_acknowledge(alert_id):
    """Acknowledge an alert."""
    success = alert_manager.acknowledge_alert(alert_id)
    
    if success:
        return jsonify({'success': True, 'alert_id': alert_id})
    else:
        return jsonify({'error': 'Alert not found'}), 404


@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST', 'DELETE'])
def api_alert_dismiss(alert_id):
    """Dismiss (remove) an alert."""
    success = alert_manager.dismiss_alert(alert_id)
    
    if success:
        return jsonify({'success': True, 'alert_id': alert_id})
    else:
        return jsonify({'error': 'Alert not found'}), 404


@app.route('/api/alerts/test', methods=['POST'])
def api_alerts_test():
    """Create a test alert (for development)."""
    data = request.get_json() or {}
    
    from alerts import AlertSeverity
    
    severity_map = {
        'info': AlertSeverity.INFO,
        'warning': AlertSeverity.WARNING,
        'critical': AlertSeverity.CRITICAL,
        'emergency': AlertSeverity.EMERGENCY,
    }
    
    severity = severity_map.get(data.get('severity', 'info'), AlertSeverity.INFO)
    
    alert = alert_manager.create_system_alert(
        title=data.get('title', 'Test Alert'),
        message=data.get('message', 'This is a test alert'),
        severity=severity,
    )
    
    return jsonify(alert.to_dict())

def main():
    global demo_mode
    
    parser = argparse.ArgumentParser(description='Air Quality Monitor API')
    parser.add_argument('--demo', action='store_true', 
                        help='Run in demo mode with simulated data')
    parser.add_argument('--port', type=int, default=PORT,
                        help=f'Server port (default: {PORT})')
    args = parser.parse_args()
    
    demo_mode = args.demo
    
    print()
    print("=" * 55)
    print("  🌡️  Air Quality Monitor")
    print("=" * 55)
    if demo_mode:
        print("  Mode: 🎮 DEMO (simulated sensor data)")
    else:
        print("  Mode: 📡 LIVE (waiting for Arduino)")
    print("=" * 55)
    print()
    
    # Initialize database
    init_db()
    
    # Load ML models
    print("🤖 Loading ML models...")
    load_results = model_manager.load_all_models()
    loaded_count = sum(1 for v in load_results.values() if v)
    print(f"   Loaded {loaded_count}/{len(load_results)} models")
    
    if loaded_count == 0:
        print("   ⚠️  No models loaded - run 'python ml/train_all.py' first")
        print("   Using rule-based predictions as fallback")
    
    # Load forecast model
    print("🔮 Loading forecast model...")
    if forecast_manager.load_model():
        print("   Forecast model ready")
    else:
        print("   ⚠️  No forecast model - run 'python -m ml.forecasting.train_forecast'")
    
    # Start data source
    if demo_mode:
        simulator.start(callback=process_reading)
    else:
        reader_thread = threading.Thread(target=serial_reader_thread, daemon=True)
        reader_thread.start()
    
    # Start Flask
    print(f"\n🚀 API Server: http://localhost:{args.port}")
    print(f"📚 Endpoints:")
    print(f"   GET  /api/health           - Health check")
    print(f"   GET  /api/latest           - Latest reading")
    print(f"   GET  /api/readings         - Historical data")
    print(f"   GET  /api/models           - Available models")
    print(f"   GET  /api/models/compare   - Model comparison")
    print(f"   POST /api/models/set       - Switch active model")
    print(f"   GET  /api/forecast         - 6-hour AQI forecast ✨")
    print(f"   GET  /api/forecast/summary - Hourly forecast summary")
    print(f"   GET  /api/alerts           - Active alerts 🚨")
    print(f"   POST /api/alerts/<id>/ack  - Acknowledge alert")
    print(f"\n💡 Frontend: http://localhost:5173 (run 'npm run dev' in frontend/)")
    print(f"\nPress Ctrl+C to stop\n")
    
    try:
        app.run(host=HOST, port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        if demo_mode:
            simulator.stop()


if __name__ == '__main__':
    main()