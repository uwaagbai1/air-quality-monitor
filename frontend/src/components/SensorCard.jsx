import React from 'react';
import { Thermometer, Droplets, Gauge, Wind } from 'lucide-react';

export default function SensorCard({ type, value, unit, color = 'blue' }) {
  // Get icon component based on type
  const getIcon = () => {
    switch (type) {
      case 'temperature':
        return <Thermometer className="w-8 h-8" />;
      case 'humidity':
        return <Droplets className="w-8 h-8" />;
      case 'pressure':
        return <Gauge className="w-8 h-8" />;
      case 'gas':
        return <Wind className="w-8 h-8" />;
      default:
        return null;
    }
  };

  // Color schemes
  const colorSchemes = {
    red: 'from-red-500/20 to-red-600/10 border-red-500/30 text-red-400',
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30 text-blue-400',
    cyan: 'from-cyan-500/20 to-cyan-600/10 border-cyan-500/30 text-cyan-400',
    green: 'from-green-500/20 to-green-600/10 border-green-500/30 text-green-400',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30 text-purple-400',
    orange: 'from-orange-500/20 to-orange-600/10 border-orange-500/30 text-orange-400',
  };

  const colorClass = colorSchemes[color] || colorSchemes.blue;

  // Labels
  const labels = {
    temperature: 'Temperature',
    humidity: 'Humidity',
    pressure: 'Pressure',
    gas: 'Gas Resistance',
  };

  const label = labels[type] || type;

  // Format value
  const formatValue = () => {
    if (value === null || value === undefined) return '--';
    if (type === 'gas') {
      return (value / 1000).toFixed(1); // Convert to kΩ
    }
    return typeof value === 'number' ? value.toFixed(1) : value;
  };

  // Get unit
  const getUnit = () => {
    if (unit) return unit;
    switch (type) {
      case 'temperature': return '°C';
      case 'humidity': return '%';
      case 'pressure': return 'hPa';
      case 'gas': return 'kΩ';
      default: return '';
    }
  };

  // Calculate progress bar width based on typical ranges
  const getProgressWidth = () => {
    if (value === null || value === undefined) return 0;
    
    switch (type) {
      case 'temperature':
        // 10-40°C range
        return Math.min(100, Math.max(0, ((value - 10) / 30) * 100));
      case 'humidity':
        // 0-100% range
        return Math.min(100, Math.max(0, value));
      case 'pressure':
        // 980-1040 hPa range
        return Math.min(100, Math.max(0, ((value - 980) / 60) * 100));
      case 'gas':
        // 0-300000 ohm range (higher is better)
        return Math.min(100, Math.max(0, (value / 300000) * 100));
      default:
        return 50;
    }
  };

  const progressWidth = getProgressWidth();

  return (
    <div className={`
      sensor-card
      bg-gradient-to-br ${colorClass}
      border rounded-xl p-4 md:p-6
    `}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm mb-1">{label}</p>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl md:text-4xl font-bold text-white">
              {formatValue()}
            </span>
            <span className="text-lg md:text-xl text-gray-400">
              {getUnit()}
            </span>
          </div>
        </div>
        
        <div className={`p-3 rounded-lg bg-gray-800/50 ${colorClass.split(' ').pop()}`}>
          {getIcon()}
        </div>
      </div>

      {/* Mini progress bar */}
      <div className="mt-4 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full rounded-full transition-all duration-500 ${
            color === 'red' ? 'bg-red-500' :
            color === 'blue' ? 'bg-blue-500' :
            color === 'cyan' ? 'bg-cyan-500' :
            color === 'green' ? 'bg-green-500' :
            color === 'purple' ? 'bg-purple-500' :
            'bg-orange-500'
          }`}
          style={{ width: `${progressWidth}%` }}
        />
      </div>
    </div>
  );
}
