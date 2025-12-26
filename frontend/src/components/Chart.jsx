import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

export default function Chart({ 
  data = null, 
  dataKey = 'value', 
  color = '#3b82f6',
  title = 'Chart',
  unit = '',
  type = 'line',
  height = 200,
}) {
  // Format timestamp for display
  const formatTime = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-2 shadow-lg">
          <p className="text-gray-400 text-xs">{formatTime(label)}</p>
          <p className="text-white font-semibold">
            {payload[0].value?.toFixed(1)} {unit}
          </p>
        </div>
      );
    }
    return null;
  };

  // Handle null/undefined data
  if (!data || !data.labels || !data[dataKey]) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
        <div className="h-[200px] flex items-center justify-center text-gray-500">
          <div className="text-center">
            <div className="animate-pulse mb-2">📊</div>
            <p>Waiting for data...</p>
          </div>
        </div>
      </div>
    );
  }

  // Prepare data for recharts
  const chartData = data.labels.map((label, idx) => ({
    time: label,
    [dataKey]: data[dataKey][idx],
  }));

  if (chartData.length === 0) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
        <div className="h-[200px] flex items-center justify-center text-gray-500">
          No data available
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={height}>
        {type === 'area' ? (
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id={`gradient-${dataKey}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              tickFormatter={formatTime}
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickFormatter={(value) => `${value}${unit}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              fill={`url(#gradient-${dataKey})`}
              strokeWidth={2}
            />
          </AreaChart>
        ) : (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis 
              dataKey="time" 
              tickFormatter={formatTime}
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <YAxis 
              stroke="#6b7280"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color }}
            />
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
