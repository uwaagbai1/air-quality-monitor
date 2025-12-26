import React, { useState, useEffect, useCallback } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  AlertCircle, 
  Info, 
  X, 
  Check,
  ChevronDown,
  ChevronUp,
  Zap,
  TrendingUp,
  Activity,
  Settings
} from 'lucide-react';

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([]);
  const [counts, setCounts] = useState({ total: 0 });
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(true);
  const [lastAlertId, setLastAlertId] = useState(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch('/api/alerts/active');
      const data = await res.json();
      
      if (data.alerts?.length > 0) {
        const newestAlert = data.alerts[0];
        if (newestAlert.id !== lastAlertId) {
          setLastAlertId(newestAlert.id);
          if (['critical', 'emergency'].includes(newestAlert.severity)) {
            playAlertSound();
          }
        }
      }
      
      setAlerts(data.alerts || []);
      setCounts(data.counts || { total: 0 });
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    } finally {
      setLoading(false);
    }
  }, [lastAlertId]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const playAlertSound = () => {
    try {
      const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2teleBoGQKHf3KViGAQ9n97do14XBDue3d2jXRYDOJ3c3aJcFQI2nNzcolsUATSb29yhWhMBM5rb3KBZEQI=');
      audio.volume = 0.5;
      audio.play().catch(() => {});
    } catch (e) {}
  };

  const acknowledgeAlert = async (alertId) => {
    try {
      await fetch(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const dismissAlert = async (alertId) => {
    try {
      await fetch(`/api/alerts/${alertId}/dismiss`, { method: 'POST' });
      setAlerts(prev => prev.filter(a => a.id !== alertId));
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const getSeverityStyle = (severity) => {
    switch (severity) {
      case 'emergency':
        return {
          icon: AlertTriangle,
          bg: 'bg-red-50 dark:bg-red-900/20',
          border: 'border-red-200 dark:border-red-800',
          text: 'text-red-600 dark:text-red-400',
          badge: 'bg-red-500',
          pulse: true,
        };
      case 'critical':
        return {
          icon: AlertCircle,
          bg: 'bg-orange-50 dark:bg-orange-900/20',
          border: 'border-orange-200 dark:border-orange-800',
          text: 'text-orange-600 dark:text-orange-400',
          badge: 'bg-orange-500',
          pulse: true,
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          bg: 'bg-amber-50 dark:bg-amber-900/20',
          border: 'border-amber-200 dark:border-amber-800',
          text: 'text-amber-600 dark:text-amber-400',
          badge: 'bg-amber-500',
          pulse: false,
        };
      default:
        return {
          icon: Info,
          bg: 'bg-blue-50 dark:bg-blue-900/20',
          border: 'border-blue-200 dark:border-blue-800',
          text: 'text-blue-600 dark:text-blue-400',
          badge: 'bg-blue-500',
          pulse: false,
        };
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'threshold': return AlertCircle;
      case 'predictive': return TrendingUp;
      case 'anomaly': return Zap;
      case 'trend': return Activity;
      case 'system': return Settings;
      default: return Info;
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };

  const hasAlerts = counts.total > 0;
  const hasCritical = (counts.critical || 0) + (counts.emergency || 0) > 0;

  return (
    <div className={`
      bg-white dark:bg-gray-800/90 border rounded-2xl overflow-hidden transition-all
      ${hasCritical 
        ? 'border-red-300 dark:border-red-800 ring-2 ring-red-100 dark:ring-red-900/30' 
        : hasAlerts 
          ? 'border-amber-200 dark:border-amber-800' 
          : 'border-gray-200 dark:border-gray-700'
      }
    `}>
      {/* Header */}
      <div 
        className={`
          flex items-center justify-between p-4 cursor-pointer transition-colors
          ${hasCritical 
            ? 'bg-red-50 dark:bg-red-900/20' 
            : hasAlerts 
              ? 'bg-amber-50/50 dark:bg-amber-900/10' 
              : 'hover:bg-gray-50 dark:hover:bg-gray-800'
          }
        `}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className={`p-2 rounded-xl ${
              hasCritical 
                ? 'bg-red-100 dark:bg-red-900/30' 
                : hasAlerts 
                  ? 'bg-amber-100 dark:bg-amber-900/30' 
                  : 'bg-gray-100 dark:bg-gray-700'
            }`}>
              <Bell className={`w-5 h-5 ${
                hasCritical 
                  ? 'text-red-600 dark:text-red-400' 
                  : hasAlerts 
                    ? 'text-amber-600 dark:text-amber-400' 
                    : 'text-gray-500 dark:text-gray-400'
              }`} />
            </div>
            {hasAlerts && (
              <span className={`
                absolute -top-1 -right-1 w-5 h-5 rounded-full text-xs flex items-center justify-center text-white font-bold
                ${hasCritical ? 'bg-red-500 animate-pulse' : 'bg-amber-500'}
              `}>
                {counts.total > 9 ? '9+' : counts.total}
              </span>
            )}
          </div>
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white">Alerts</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {hasAlerts 
                ? `${counts.total} active alert${counts.total !== 1 ? 's' : ''}`
                : 'No active alerts'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <div className="p-1">
            {expanded 
              ? <ChevronUp className="w-5 h-5 text-gray-400" />
              : <ChevronDown className="w-5 h-5 text-gray-400" />
            }
          </div>
        </div>
      </div>

      {/* Alert list */}
      {expanded && (
        <div className="border-t border-gray-100 dark:border-gray-700">
          {loading ? (
            <div className="p-6 text-center text-gray-500 dark:text-gray-400">
              <div className="animate-pulse">Loading alerts...</div>
            </div>
          ) : alerts.length === 0 ? (
            <div className="p-8 text-center">
              <div className="w-12 h-12 mx-auto mb-3 bg-emerald-100 dark:bg-emerald-900/30 rounded-full flex items-center justify-center">
                <Bell className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
              </div>
              <p className="text-gray-700 dark:text-gray-300 font-medium">All clear!</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">No active alerts at this time</p>
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto">
              {alerts.map((alert) => {
                const style = getSeverityStyle(alert.severity);
                const Icon = style.icon;
                const TypeIcon = getTypeIcon(alert.type);
                
                return (
                  <div
                    key={alert.id}
                    className={`p-4 border-b border-gray-100 dark:border-gray-700 last:border-0 ${style.bg}`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-xl border ${style.bg} ${style.border} ${style.pulse ? 'animate-pulse' : ''}`}>
                        <Icon className={`w-4 h-4 ${style.text}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className={`font-semibold ${style.text}`}>
                            {alert.title}
                          </span>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold ${style.badge} text-white`}>
                            {alert.severity}
                          </span>
                          <TypeIcon className="w-3 h-3 text-gray-400" />
                        </div>
                        
                        <p className="text-sm text-gray-600 dark:text-gray-300 mb-2">
                          {alert.message}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {formatTime(alert.timestamp)}
                            {alert.aqi_value && <span className="ml-2">• AQI: {alert.aqi_value}</span>}
                          </span>
                          
                          <div className="flex items-center gap-1">
                            <button
                              onClick={() => acknowledgeAlert(alert.id)}
                              className="p-1.5 rounded-lg hover:bg-emerald-100 dark:hover:bg-emerald-900/30 transition-colors"
                              title="Acknowledge"
                            >
                              <Check className="w-4 h-4 text-emerald-500" />
                            </button>
                            <button
                              onClick={() => dismissAlert(alert.id)}
                              className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                              title="Dismiss"
                            >
                              <X className="w-4 h-4 text-gray-400" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}