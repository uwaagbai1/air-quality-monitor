import React, { useState, useEffect } from 'react';
import { TrendingUp, Clock, AlertTriangle, RefreshCw, CloudRain, Sparkles } from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  ComposedChart,
  Line,
} from 'recharts';

export default function ForecastChart() {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchForecast = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/forecast');
      const data = await res.json();
      
      if (data.error) {
        setError(data.error);
        setForecast(null);
      } else {
        setForecast(data);
        setError(null);
        setLastUpdated(new Date());
      }
    } catch (err) {
      setError('Failed to load forecast');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
    const interval = setInterval(fetchForecast, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  const getAqiCategory = (aqi) => {
    if (aqi <= 50) return { label: 'Good', color: '#10b981' };
    if (aqi <= 100) return { label: 'Moderate', color: '#f59e0b' };
    if (aqi <= 150) return { label: 'Unhealthy for Sensitive', color: '#f97316' };
    if (aqi <= 200) return { label: 'Unhealthy', color: '#ef4444' };
    if (aqi <= 300) return { label: 'Very Unhealthy', color: '#a855f7' };
    return { label: 'Hazardous', color: '#991b1b' };
  };

  const formatChartData = (forecastData) => {
    if (!forecastData?.forecast) return [];
    
    return forecastData.forecast.map((point) => ({
      ...point,
      time: `+${point.hours_ahead}h`,
      displayTime: point.hours_ahead < 1 
        ? `${Math.round(point.hours_ahead * 60)}m` 
        : `${point.hours_ahead}h`,
    }));
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    
    const data = payload[0].payload;
    const category = getAqiCategory(data.aqi);
    
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl p-3 shadow-xl">
        <div className="text-gray-500 dark:text-gray-400 text-sm mb-1">
          {data.hours_ahead < 1 
            ? `In ${Math.round(data.hours_ahead * 60)} minutes`
            : `In ${data.hours_ahead} hours`}
        </div>
        <div className="flex items-center gap-2">
          <span 
            className="w-3 h-3 rounded-full" 
            style={{ backgroundColor: category.color }}
          />
          <span className="text-gray-900 dark:text-white font-bold text-lg">{data.aqi}</span>
          <span className="text-gray-400 text-sm">AQI</span>
        </div>
        <div className="text-sm mt-1 font-medium" style={{ color: category.color }}>
          {category.label}
        </div>
      </div>
    );
  };

  if (loading && !forecast) {
    return (
      <div className="bg-white dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 rounded-2xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/3"></div>
          <div className="h-56 bg-gray-100 dark:bg-gray-700 rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
            <TrendingUp className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">AQI Forecast</h3>
        </div>
        <div className="text-center py-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
            <CloudRain className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-600 dark:text-gray-400 font-medium mb-2">{error}</p>
          {error.includes('Not enough') && (
            <p className="text-sm text-gray-500 dark:text-gray-500">
              Keep collecting data - forecast needs 50+ readings
            </p>
          )}
          {error.includes('not loaded') && (
            <div className="mt-2">
              <code className="text-xs bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-lg text-gray-600 dark:text-gray-300">
                python -m ml.forecasting.train_forecast
              </code>
            </div>
          )}
          <button
            onClick={fetchForecast}
            className="mt-4 px-4 py-2 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-xl 
                     hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors inline-flex items-center gap-2 font-medium"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    );
  }

  const chartData = formatChartData(forecast);
  const summary = forecast?.summary || {};
  const maxAqi = summary.max_aqi || 0;
  const trend = summary.trend || 'stable';

  return (
    <div className="bg-white dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 rounded-2xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-xl">
            <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">6-Hour Forecast</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">LSTM neural network prediction</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Trend indicator */}
          <div className={`
            text-xs px-3 py-1.5 rounded-full flex items-center gap-1.5 font-semibold
            ${trend === 'improving' 
              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400' 
              : trend === 'worsening' 
                ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' 
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }
          `}>
            <TrendingUp className={`w-3 h-3 ${trend === 'worsening' ? 'rotate-180' : ''}`} />
            {trend.charAt(0).toUpperCase() + trend.slice(1)}
          </div>
          
          <button
            onClick={fetchForecast}
            disabled={loading}
            className="p-2 rounded-xl bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 
                     transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Alert if high AQI predicted */}
      {summary.alert && (
        <div className={`
          mb-4 p-3 rounded-xl flex items-center gap-3
          ${summary.alert.severity === 'critical' 
            ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' 
            : 'bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800'}
        `}>
          <AlertTriangle className={`w-5 h-5 ${
            summary.alert.severity === 'critical' 
              ? 'text-red-600 dark:text-red-400' 
              : 'text-orange-600 dark:text-orange-400'
          }`} />
          <span className="text-sm text-gray-700 dark:text-gray-200">{summary.alert.message}</span>
        </div>
      )}

      {/* Chart */}
      <div className="h-64 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData}>
            <defs>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:opacity-20" />
            <XAxis 
              dataKey="displayTime" 
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#9ca3af"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
              tickLine={false}
              axisLine={false}
              domain={[0, Math.max(100, maxAqi + 20)]}
            />
            <Tooltip content={<CustomTooltip />} />
            
            {/* AQI threshold lines */}
            <ReferenceLine y={50} stroke="#10b981" strokeDasharray="3 3" strokeOpacity={0.5} />
            <ReferenceLine y={100} stroke="#f59e0b" strokeDasharray="3 3" strokeOpacity={0.5} />
            <ReferenceLine y={150} stroke="#f97316" strokeDasharray="3 3" strokeOpacity={0.5} />
            
            <Area
              type="monotone"
              dataKey="aqi"
              stroke="transparent"
              fill="url(#forecastGradient)"
            />
            <Line
              type="monotone"
              dataKey="aqi"
              stroke="#8b5cf6"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, fill: '#8b5cf6', stroke: '#fff', strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100 dark:border-gray-700">
        <div className="text-center">
          <div className="text-2xl font-black text-gray-900 dark:text-white">{summary.avg_aqi || '--'}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">Avg AQI</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-black text-emerald-500">{summary.min_aqi || '--'}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            Min (in {summary.min_at_hours || '--'}h)
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-black text-red-500">{summary.max_aqi || '--'}</div>
          <div className="text-xs text-gray-500 dark:text-gray-400 font-medium">
            Max (in {summary.max_at_hours || '--'}h)
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>Updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}</span>
        </div>
        <div className="font-medium">
          Model: {forecast?.model || 'LSTM'}
        </div>
      </div>
    </div>
  );
}
