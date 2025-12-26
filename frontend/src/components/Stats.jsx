import React from 'react';
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react';

export default function Stats({ stats, loading = false }) {
  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-1/3"></div>
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-16 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">24-Hour Statistics</h3>
        </div>
        <p className="text-gray-500">No statistics available yet</p>
      </div>
    );
  }

  const statItems = [
    {
      label: 'Readings',
      value: stats.reading_count || 0,
      unit: '',
      color: 'text-blue-400',
    },
    {
      label: 'Avg Temp',
      value: stats.temperature?.avg || '--',
      unit: '°C',
      min: stats.temperature?.min,
      max: stats.temperature?.max,
      color: 'text-red-400',
    },
    {
      label: 'Avg Humidity',
      value: stats.humidity?.avg || '--',
      unit: '%',
      min: stats.humidity?.min,
      max: stats.humidity?.max,
      color: 'text-cyan-400',
    },
    {
      label: 'Avg AQI',
      value: stats.aqi?.avg || '--',
      unit: '',
      min: stats.aqi?.min,
      max: stats.aqi?.max,
      color: 'text-green-400',
    },
  ];

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-gray-400" />
          <h3 className="text-lg font-semibold text-white">24-Hour Statistics</h3>
        </div>
        {stats.avg_inference_time_ms && (
          <span className="text-xs text-gray-500">
            Avg inference: {stats.avg_inference_time_ms}ms
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statItems.map((item, idx) => (
          <div key={idx} className="bg-gray-700/50 rounded-lg p-3">
            <p className="text-gray-400 text-sm mb-1">{item.label}</p>
            <p className={`text-2xl font-bold ${item.color}`}>
              {item.value}
              <span className="text-sm text-gray-400 ml-1">{item.unit}</span>
            </p>
            
            {/* Min/Max range */}
            {item.min !== undefined && item.max !== undefined && (
              <p className="text-xs text-gray-500 mt-1">
                {item.min}{item.unit} — {item.max}{item.unit}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
