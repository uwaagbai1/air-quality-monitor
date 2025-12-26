import os

# Flask settings
HOST = '0.0.0.0'
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), 'readings.db')

# Serial (Arduino)
SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/ttyUSB0')
SERIAL_BAUD = 115200

# Demo mode
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'
DEMO_INTERVAL = 3  # seconds between simulated readings

# CORS - allow React frontend
CORS_ORIGINS = [
    'http://localhost:5173',  # Vite dev server
    'http://localhost:3000',
    'http://127.0.0.1:5173',
    'http://127.0.0.1:3000',
]

# Sensor thresholds
AQI_THRESHOLDS = {
    'good': (0, 50),
    'moderate': (51, 100),
    'unhealthy_sensitive': (101, 150),
    'unhealthy': (151, 200),
    'very_unhealthy': (201, 300),
    'hazardous': (301, 500),
}

MODELS_DIR = os.path.join(os.path.dirname(__file__), 'ml', 'models')
DEFAULT_MODEL = 'random_forest'
