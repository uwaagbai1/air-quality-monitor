import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from config import DB_PATH


def init_db():
    # Initialize database with required tables
    with get_db() as db:
        # Main readings table
        db.execute('''
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id TEXT DEFAULT 'default',
                location TEXT DEFAULT 'Room',
                temperature REAL,
                humidity REAL,
                pressure REAL,
                gas_resistance REAL,
                aqi INTEGER,
                prediction_category INTEGER,
                prediction_label TEXT,
                prediction_confidence REAL,
                model_used TEXT,
                inference_time_ms REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Alerts table
        db.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT,
                severity TEXT,
                message TEXT,
                reading_id INTEGER,
                acknowledged INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (reading_id) REFERENCES readings(id)
            )
        ''')
        
        # Model metrics table for tracking model performance
        db.execute('''
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                accuracy REAL,
                inference_time_ms REAL,
                model_size_kb REAL,
                energy_mj REAL,
                trained_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for performance
        db.execute('CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON readings(timestamp)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_readings_node ON readings(node_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at)')
        
        db.commit()
    
    print(f"✅ Database initialized: {DB_PATH}")


@contextmanager
def get_db():
    # Thread-safe database connection context manager
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_reading(data: Dict[str, Any]) -> int:
    # Save a sensor reading to database. Returns reading ID
    with get_db() as db:
        cursor = db.execute('''
            INSERT INTO readings 
            (node_id, location, temperature, humidity, pressure, 
             gas_resistance, aqi, prediction_category, prediction_label,
             prediction_confidence, model_used, inference_time_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('node_id', 'default'),
            data.get('location', 'Room'),
            data.get('temperature'),
            data.get('humidity'),
            data.get('pressure'),
            data.get('gas_resistance'),
            data.get('aqi'),
            data.get('prediction', {}).get('category'),
            data.get('prediction', {}).get('label'),
            data.get('prediction', {}).get('confidence'),
            data.get('model_used', 'rule_based'),
            data.get('inference_time_ms'),
        ))
        db.commit()
        return cursor.lastrowid


def get_latest_reading() -> Optional[Dict]:
    # Get the most recent reading
    with get_db() as db:
        row = db.execute('''
            SELECT * FROM readings ORDER BY timestamp DESC LIMIT 1
        ''').fetchone()
    
    return dict(row) if row else None


def get_readings(hours: int = 24, limit: int = 500) -> List[Dict]:
    # Get readings from the last N hours
    since = datetime.now() - timedelta(hours=hours)
    
    with get_db() as db:
        rows = db.execute('''
            SELECT * FROM readings 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (since.isoformat(), limit)).fetchall()
    
    return [dict(row) for row in rows]


def get_readings_for_chart(hours: int = 24) -> Dict[str, List]:
    # Get readings formatted for charts
    since = datetime.now() - timedelta(hours=hours)
    
    with get_db() as db:
        rows = db.execute('''
            SELECT timestamp, temperature, humidity, pressure, aqi
            FROM readings
            WHERE timestamp > ?
            ORDER BY timestamp ASC
        ''', (since.isoformat(),)).fetchall()
    
    return {
        'labels': [row['timestamp'] for row in rows],
        'temperature': [row['temperature'] for row in rows],
        'humidity': [row['humidity'] for row in rows],
        'pressure': [row['pressure'] for row in rows],
        'aqi': [row['aqi'] for row in rows],
    }


def get_stats(hours: int = 24) -> Dict[str, Any]:
    # Get aggregated statistics for the last N hours
    since = datetime.now() - timedelta(hours=hours)
    
    with get_db() as db:
        row = db.execute('''
            SELECT 
                COUNT(*) as count,
                AVG(temperature) as avg_temp,
                MIN(temperature) as min_temp,
                MAX(temperature) as max_temp,
                AVG(humidity) as avg_humidity,
                MIN(humidity) as min_humidity,
                MAX(humidity) as max_humidity,
                AVG(aqi) as avg_aqi,
                MIN(aqi) as min_aqi,
                MAX(aqi) as max_aqi,
                AVG(inference_time_ms) as avg_inference_time
            FROM readings
            WHERE timestamp > ?
        ''', (since.isoformat(),)).fetchone()
    
    return {
        'period_hours': hours,
        'reading_count': row['count'] or 0,
        'temperature': {
            'avg': round(row['avg_temp'] or 0, 1),
            'min': round(row['min_temp'] or 0, 1),
            'max': round(row['max_temp'] or 0, 1),
        },
        'humidity': {
            'avg': round(row['avg_humidity'] or 0, 1),
            'min': round(row['min_humidity'] or 0, 1),
            'max': round(row['max_humidity'] or 0, 1),
        },
        'aqi': {
            'avg': round(row['avg_aqi'] or 0),
            'min': row['min_aqi'] or 0,
            'max': row['max_aqi'] or 0,
        },
        'avg_inference_time_ms': round(row['avg_inference_time'] or 0, 2),
    }


def save_alert(alert_type: str, severity: str, message: str, reading_id: int = None) -> int:
    # Save an alert to database
    with get_db() as db:
        cursor = db.execute('''
            INSERT INTO alerts (alert_type, severity, message, reading_id)
            VALUES (?, ?, ?, ?)
        ''', (alert_type, severity, message, reading_id))
        db.commit()
        return cursor.lastrowid


def get_active_alerts(limit: int = 50) -> List[Dict]:
    # Get unacknowledged alerts
    with get_db() as db:
        rows = db.execute('''
            SELECT * FROM alerts 
            WHERE acknowledged = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,)).fetchall()
    
    return [dict(row) for row in rows]
