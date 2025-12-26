import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque
from dataclasses import dataclass, asdict
from enum import Enum


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    THRESHOLD = "threshold"
    PREDICTIVE = "predictive"
    ANOMALY = "anomaly"
    SYSTEM = "system"
    TREND = "trend"


@dataclass
class Alert:
    """Alert data structure."""
    id: str
    type: str
    severity: str
    title: str
    message: str
    timestamp: str
    reading_id: Optional[int] = None
    aqi_value: Optional[int] = None
    acknowledged: bool = False
    auto_dismiss: bool = False
    expires_at: Optional[str] = None
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class AlertManager:
    
    # AQI Thresholds (EPA standard)
    THRESHOLDS = {
        'good': (0, 50),
        'moderate': (51, 100),
        'unhealthy_sensitive': (101, 150),
        'unhealthy': (151, 200),
        'very_unhealthy': (201, 300),
        'hazardous': (301, 500),
    }
    
    # Alert configurations
    CONFIG = {
        'threshold_cooldown_minutes': 15,      # Min time between same threshold alerts
        'anomaly_window_size': 10,             # Readings to consider for anomaly
        'anomaly_std_threshold': 3.0,          # Standard deviations for anomaly
        'predictive_lead_time_hours': 2,       # Alert this many hours before bad air
        'max_active_alerts': 50,               # Maximum alerts to keep
        'alert_history_hours': 24,             # Keep alerts for this long
    }
    
    def __init__(self, db_save_func=None, db_load_func=None):
        """
        Initialize alert manager.
        
        Args:
            db_save_func: Function to save alerts to database
            db_load_func: Function to load alerts from database
        """
        self.active_alerts: List[Alert] = []
        self.alert_history: deque = deque(maxlen=500)
        self.reading_buffer: deque = deque(maxlen=50)  # Recent readings for anomaly detection
        
        # Track last alert times to prevent spam
        self.last_alert_times: Dict[str, datetime] = {}
        
        # Callbacks for alert notifications
        self.callbacks: List[callable] = []
        
        # Alert counter for unique IDs
        self._alert_counter = 0
        
        # Database functions (optional)
        self.db_save = db_save_func
        self.db_load = db_load_func
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        self._alert_counter += 1
        return f"alert_{datetime.now().strftime('%Y%m%d%H%M%S')}_{self._alert_counter}"
    
    def _can_send_alert(self, alert_key: str) -> bool:
        # Check if we can send this type of alert (rate limiting)
        now = datetime.now()
        cooldown = timedelta(minutes=self.CONFIG['threshold_cooldown_minutes'])
        
        if alert_key in self.last_alert_times:
            if now - self.last_alert_times[alert_key] < cooldown:
                return False
        
        self.last_alert_times[alert_key] = now
        return True
    
    def _get_aqi_category(self, aqi: int) -> tuple:
        # Get AQI category name and info.
        for category, (low, high) in self.THRESHOLDS.items():
            if low <= aqi <= high:
                return category, low, high
        return 'hazardous', 301, 500
    
    def _create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        reading_id: int = None,
        aqi_value: int = None,
        auto_dismiss: bool = False,
        expires_minutes: int = None,
        metadata: Dict = None,
    ) -> Alert:
        # Create and store a new alert.
        
        expires_at = None
        if expires_minutes:
            expires_at = (datetime.now() + timedelta(minutes=expires_minutes)).isoformat()
        
        alert = Alert(
            id=self._generate_alert_id(),
            type=alert_type.value,
            severity=severity.value,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            reading_id=reading_id,
            aqi_value=aqi_value,
            auto_dismiss=auto_dismiss,
            expires_at=expires_at,
            metadata=metadata or {},
        )
        
        # Add to active alerts
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Trim old alerts
        self._cleanup_alerts()
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
        
        # Save to database if available
        if self.db_save:
            try:
                self.db_save(alert.to_dict())
            except Exception as e:
                print(f"Failed to save alert to DB: {e}")
        
        return alert
    
    def _cleanup_alerts(self):
        # Remove expired and old alerts.
        now = datetime.now()
        cutoff = now - timedelta(hours=self.CONFIG['alert_history_hours'])
        
        # Remove expired alerts
        self.active_alerts = [
            a for a in self.active_alerts
            if not a.expires_at or datetime.fromisoformat(a.expires_at) > now
        ]
        
        # Remove acknowledged alerts older than 1 hour
        one_hour_ago = now - timedelta(hours=1)
        self.active_alerts = [
            a for a in self.active_alerts
            if not a.acknowledged or datetime.fromisoformat(a.timestamp) > one_hour_ago
        ]
        
        # Limit total active alerts
        if len(self.active_alerts) > self.CONFIG['max_active_alerts']:
            self.active_alerts = self.active_alerts[-self.CONFIG['max_active_alerts']:]
        
    def process_reading(self, reading: Dict[str, Any]) -> List[Alert]:
  
        new_alerts = []
        
        # Store reading for anomaly detection
        self.reading_buffer.append(reading)
        
        aqi = reading.get('aqi', 0)
        reading_id = reading.get('id')
        
        # 1. Check threshold alerts
        threshold_alert = self._check_threshold(aqi, reading_id)
        if threshold_alert:
            new_alerts.append(threshold_alert)
        
        # 2. Check for anomalies
        anomaly_alert = self._check_anomaly(reading)
        if anomaly_alert:
            new_alerts.append(anomaly_alert)
        
        # 3. Check trend alerts
        trend_alert = self._check_trend()
        if trend_alert:
            new_alerts.append(trend_alert)
        
        return new_alerts
    
    def process_forecast(self, forecast: Dict[str, Any]) -> List[Alert]:
        
        new_alerts = []
        
        if not forecast or 'forecast' not in forecast:
            return new_alerts
        
        predictions = forecast['forecast']
        lead_time = self.CONFIG['predictive_lead_time_hours']
        
        # Check predictions within lead time
        for pred in predictions:
            hours_ahead = pred.get('hours_ahead', 0)
            aqi = pred.get('aqi', 0)
            
            if hours_ahead <= lead_time:
                # Check if AQI will cross into unhealthy territory
                if aqi > 150:
                    alert_key = f"predictive_{int(aqi / 50) * 50}"  # Group by 50s
                    
                    if self._can_send_alert(alert_key):
                        severity = AlertSeverity.CRITICAL if aqi > 200 else AlertSeverity.WARNING
                        
                        alert = self._create_alert(
                            alert_type=AlertType.PREDICTIVE,
                            severity=severity,
                            title=f"AQI Expected to Reach {aqi}",
                            message=f"Air quality forecast predicts AQI of {aqi} in {hours_ahead:.1f} hours. Consider staying indoors.",
                            aqi_value=aqi,
                            auto_dismiss=True,
                            expires_minutes=int(hours_ahead * 60),
                            metadata={
                                'hours_ahead': hours_ahead,
                                'timestamp': pred.get('timestamp'),
                            }
                        )
                        new_alerts.append(alert)
                        break  # One predictive alert at a time
        
        return new_alerts
    
    def _check_threshold(self, aqi: int, reading_id: int = None) -> Optional[Alert]:
        # Check if AQI crosses a threshold.
        category, low, high = self._get_aqi_category(aqi)
        
        # Only alert for concerning levels
        if category in ['good', 'moderate']:
            return None
        
        alert_key = f"threshold_{category}"
        
        if not self._can_send_alert(alert_key):
            return None
        
        # Determine severity
        severity_map = {
            'unhealthy_sensitive': AlertSeverity.WARNING,
            'unhealthy': AlertSeverity.CRITICAL,
            'very_unhealthy': AlertSeverity.CRITICAL,
            'hazardous': AlertSeverity.EMERGENCY,
        }
        severity = severity_map.get(category, AlertSeverity.INFO)
        
        # Create message
        messages = {
            'unhealthy_sensitive': "Air quality is unhealthy for sensitive groups. People with respiratory conditions should limit outdoor activities.",
            'unhealthy': "Air quality is unhealthy. Everyone should reduce prolonged outdoor exertion.",
            'very_unhealthy': "Air quality is very unhealthy. Avoid outdoor activities.",
            'hazardous': "HAZARDOUS air quality! Stay indoors with windows closed. Use air filtration if available.",
        }
        
        titles = {
            'unhealthy_sensitive': "⚠️ Unhealthy for Sensitive Groups",
            'unhealthy': "🔴 Unhealthy Air Quality",
            'very_unhealthy': "🟣 Very Unhealthy Air Quality",
            'hazardous': "☠️ HAZARDOUS Air Quality",
        }
        
        return self._create_alert(
            alert_type=AlertType.THRESHOLD,
            severity=severity,
            title=titles.get(category, "Air Quality Alert"),
            message=messages.get(category, f"AQI is {aqi}"),
            reading_id=reading_id,
            aqi_value=aqi,
            auto_dismiss=False,
            metadata={'category': category}
        )
    
    def _check_anomaly(self, reading: Dict) -> Optional[Alert]:
        # Detect anomalous readings (sudden changes)
        if len(self.reading_buffer) < self.CONFIG['anomaly_window_size']:
            return None
        
        aqi_values = [r.get('aqi', 0) for r in list(self.reading_buffer)[-self.CONFIG['anomaly_window_size']:]]
        
        if len(aqi_values) < 3:
            return None
        
        # Calculate statistics
        import statistics
        mean = statistics.mean(aqi_values[:-1])  # Exclude current
        stdev = statistics.stdev(aqi_values[:-1]) if len(aqi_values) > 2 else 10
        
        current = aqi_values[-1]
        
        # Check if current reading is anomalous
        if stdev > 0:
            z_score = abs(current - mean) / stdev
            
            if z_score > self.CONFIG['anomaly_std_threshold']:
                alert_key = "anomaly"
                
                if self._can_send_alert(alert_key):
                    direction = "spike" if current > mean else "drop"
                    change = abs(current - mean)
                    
                    return self._create_alert(
                        alert_type=AlertType.ANOMALY,
                        severity=AlertSeverity.WARNING,
                        title=f"Unusual AQI {direction.capitalize()}",
                        message=f"AQI changed by {change:.0f} points ({direction}). Current: {current}, Recent average: {mean:.0f}",
                        aqi_value=current,
                        auto_dismiss=True,
                        expires_minutes=30,
                        metadata={
                            'z_score': round(z_score, 2),
                            'mean': round(mean, 1),
                            'stdev': round(stdev, 1),
                            'direction': direction,
                        }
                    )
        
        return None
    
    def _check_trend(self) -> Optional[Alert]:
        # Check for sustained trends
        if len(self.reading_buffer) < 20:
            return None
        
        recent = [r.get('aqi', 0) for r in list(self.reading_buffer)[-20:]]
        
        # Check for sustained increase
        first_half = sum(recent[:10]) / 10
        second_half = sum(recent[10:]) / 10
        
        change_pct = ((second_half - first_half) / first_half * 100) if first_half > 0 else 0
        
        if change_pct > 30:  # 30% increase
            alert_key = "trend_worsening"
            
            if self._can_send_alert(alert_key):
                return self._create_alert(
                    alert_type=AlertType.TREND,
                    severity=AlertSeverity.WARNING,
                    title="Air Quality Worsening",
                    message=f"AQI has increased by {change_pct:.0f}% over recent readings. Consider taking precautions.",
                    aqi_value=int(second_half),
                    auto_dismiss=True,
                    expires_minutes=60,
                    metadata={
                        'change_percent': round(change_pct, 1),
                        'from_avg': round(first_half, 1),
                        'to_avg': round(second_half, 1),
                    }
                )
        
        return None
    
    def create_system_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.WARNING,
    ) -> Alert:
        # Create a system alert (sensor issues, etc.).
        return self._create_alert(
            alert_type=AlertType.SYSTEM,
            severity=severity,
            title=title,
            message=message,
            auto_dismiss=True,
            expires_minutes=60,
        )
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        # Acknowledge an alert
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def dismiss_alert(self, alert_id: str) -> bool:
        # Dismiss (remove) an alert.
        self.active_alerts = [a for a in self.active_alerts if a.id != alert_id]
        return True
    
    def get_active_alerts(self) -> List[Dict]:
        # Get all active (unacknowledged) alerts
        self._cleanup_alerts()
        return [a.to_dict() for a in self.active_alerts if not a.acknowledged]
    
    def get_all_alerts(self, include_acknowledged: bool = True) -> List[Dict]:
        # Get all alerts
        self._cleanup_alerts()
        if include_acknowledged:
            return [a.to_dict() for a in self.active_alerts]
        return [a.to_dict() for a in self.active_alerts if not a.acknowledged]
    
    def get_alert_counts(self) -> Dict[str, int]:
        # Get counts by severity
        counts = {'total': 0, 'info': 0, 'warning': 0, 'critical': 0, 'emergency': 0}
        
        for alert in self.active_alerts:
            if not alert.acknowledged:
                counts['total'] += 1
                counts[alert.severity] = counts.get(alert.severity, 0) + 1
        
        return counts
    
    def register_callback(self, callback: callable):
        # Register a callback for new alerts
        self.callbacks.append(callback)
    
    def clear_all(self):
        # Clear all alerts (for testing)
        self.active_alerts = []
        self.last_alert_times = {}


# Global instance
alert_manager = AlertManager()
