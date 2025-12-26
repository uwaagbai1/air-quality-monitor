import math
import random
import time
import threading
from datetime import datetime
from typing import Dict, Any, Callable, Optional

from config import DEMO_INTERVAL


class SensorSimulator:
    # Simulates BME680 sensor readings with realistic patterns
    
    def __init__(self):
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.callback: Optional[Callable] = None
        self.reading_count = 0
        
        # Base values
        self.base_temp = 22.0
        self.base_humidity = 45.0
        self.base_pressure = 1013.0
        self.base_gas = 150000  # Good air quality
        
        # Simulation state
        self.pollution_event = False
        self.pollution_start = 0
        
    def start(self, callback: Callable[[Dict[str, Any]], None]):
        # Start generating simulated data
        self.running = True
        self.callback = callback
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("🎮 Demo simulator started")
        
    def stop(self):
        # Stop the simulator
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("🎮 Demo simulator stopped")
        
    def _run(self):
        # Main simulation loop
        while self.running:
            reading = self.generate_reading()
            if self.callback:
                self.callback(reading)
            time.sleep(DEMO_INTERVAL)
            
    def generate_reading(self) -> Dict[str, Any]:
        # Generate a single simulated reading
        self.reading_count += 1
        t = time.time()
        
        # Time-based factors for realistic daily patterns
        hour_factor = math.sin(t / 3600 * math.pi / 12)  # 24-hour cycle
        minute_factor = math.sin(t / 60 * math.pi)  # Small fluctuations
        
        # Random pollution events (10% chance every reading)
        if not self.pollution_event and random.random() < 0.03:
            self.pollution_event = True
            self.pollution_start = t
            print("   🌫️ Simulating pollution event...")
            
        # End pollution event after 30-90 seconds
        if self.pollution_event and (t - self.pollution_start) > random.uniform(30, 90):
            self.pollution_event = False
            print("   🌬️ Pollution event ended")
        
        # Temperature: 18-28°C with daily cycle
        temperature = (
            self.base_temp 
            + 5 * hour_factor 
            + random.uniform(-0.3, 0.3) 
            + 0.2 * minute_factor
        )
        
        # Humidity: inversely related to temperature, 30-70%
        humidity = (
            self.base_humidity 
            - 15 * hour_factor 
            + random.uniform(-1, 1)
        )
        humidity = max(25, min(75, humidity))
        
        # Pressure: slow drift 1005-1025 hPa
        pressure = (
            self.base_pressure 
            + 8 * math.sin(t / 10000) 
            + random.uniform(-0.3, 0.3)
        )
        
        # Gas resistance: higher = cleaner air
        if self.pollution_event:
            # Poor air during pollution event
            gas_resistance = random.uniform(25000, 60000)
        else:
            gas_resistance = (
                self.base_gas 
                + 40000 * hour_factor  # Better air in afternoon
                + random.uniform(-8000, 8000)
            )
        gas_resistance = max(15000, gas_resistance)
        
        # Calculate AQI from gas resistance
        aqi = self._calculate_aqi(gas_resistance, humidity)
        
        return {
            'type': 'reading',
            'node_id': 'demo_simulator',
            'location': 'Demo Room',
            'temperature': round(temperature, 2),
            'humidity': round(humidity, 2),
            'pressure': round(pressure, 2),
            'gas_resistance': round(gas_resistance, 0),
            'aqi': aqi,
            'timestamp': datetime.now().isoformat(),
            'is_demo': True,
        }
    
    def _calculate_aqi(self, gas_resistance: float, humidity: float) -> int:
        """
        Calculate AQI from gas resistance.
        Higher resistance = cleaner air = lower AQI
        REALISTIC INDOOR CALIBRATION
        """
        # Humidity compensation (gas sensor affected by humidity)
        humidity_factor = 1.0 + (humidity - 50) * 0.002
        compensated_gas = gas_resistance * humidity_factor
        
        # Realistic indoor thresholds
        # Typical indoor: 30,000 - 150,000 ohms
        if compensated_gas > 150000:
            aqi = random.randint(0, 25)    # Excellent - very clean air
        elif compensated_gas > 100000:
            aqi = random.randint(25, 50)     # Good - well ventilated
        elif compensated_gas > 70000:
            aqi = random.randint(50, 75)     # Moderate - normal indoor
        elif compensated_gas > 50000:
            aqi = random.randint(75, 100)    # Moderate - typical room
        elif compensated_gas > 35000:
            aqi = random.randint(100, 150)   # Unhealthy-Sensitive - stuffy
        elif compensated_gas > 20000:
            aqi = random.randint(150, 200)   # Unhealthy - poor ventilation
        else:
            aqi = random.randint(200, 300)   # Very Unhealthy
            
        return min(500, max(0, aqi))


def get_aqi_category(aqi: int) -> Dict[str, Any]:
    """Get AQI category information."""
    if aqi <= 50:
        return {
            'category': 0,
            'label': 'Good',
            'color': '#00e400',
            'text_color': '#000000',
            'recommendation': 'Air quality is satisfactory. Enjoy outdoor activities!'
        }
    elif aqi <= 100:
        return {
            'category': 1,
            'label': 'Moderate',
            'color': '#ffff00',
            'text_color': '#000000',
            'recommendation': 'Air quality is acceptable. Sensitive individuals should limit prolonged outdoor exertion.'
        }
    elif aqi <= 150:
        return {
            'category': 2,
            'label': 'Unhealthy for Sensitive Groups',
            'color': '#ff7e00',
            'text_color': '#ffffff',
            'recommendation': 'People with respiratory conditions should reduce outdoor activity.'
        }
    elif aqi <= 200:
        return {
            'category': 3,
            'label': 'Unhealthy',
            'color': '#ff0000',
            'text_color': '#ffffff',
            'recommendation': 'Everyone may experience health effects. Limit outdoor exertion.'
        }
    elif aqi <= 300:
        return {
            'category': 4,
            'label': 'Very Unhealthy',
            'color': '#8f3f97',
            'text_color': '#ffffff',
            'recommendation': 'Health alert! Everyone should avoid outdoor activities.'
        }
    else:
        return {
            'category': 5,
            'label': 'Hazardous',
            'color': '#7e0023',
            'text_color': '#ffffff',
            'recommendation': 'Emergency conditions! Stay indoors with air filtration.'
        }


# Singleton instance
simulator = SensorSimulator()
