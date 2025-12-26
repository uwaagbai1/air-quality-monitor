import React, { useState, useEffect } from 'react';
import Header from './Header';
import AqiGauge from './AqiGauge';
import SensorCard from './SensorCard';
import PredictionCard from './PredictionCard';
import ModelSelector from './ModelSelector';
import ModelComparison from './ModelComparison';
import Chart from './Chart';
import Stats from './Stats';
import ForecastChart from './ForecastChart';
import AlertPanel from './AlertPanel';
import AIInsights from './AIInsights';
import { useSensorData, useChartData, useStats } from '../hooks/useSensorData';

export default function Dashboard() {
  // Data hooks
  const { latest, loading, error, isConnected, mode } = useSensorData(3000);
  const { data: chartData } = useChartData(24, 60000);
  const { stats } = useStats(24, 60000);

  // Model selection
  const [activeModel, setActiveModel] = useState('random_forest');
  
  // Forecast and alerts state for AI Insights
  const [forecast, setForecast] = useState(null);
  const [alerts, setAlerts] = useState([]);

  // Fetch forecast data
  useEffect(() => {
    const fetchForecast = async () => {
      try {
        const res = await fetch('/api/forecast');
        const data = await res.json();
        if (!data.error) setForecast(data);
      } catch (e) {}
    };
    fetchForecast();
    const interval = setInterval(fetchForecast, 60000); // Every minute
    return () => clearInterval(interval);
  }, []);

  // Fetch alerts data
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch('/api/alerts/active');
        const data = await res.json();
        setAlerts(data.alerts || []);
      } catch (e) {}
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Every 10 seconds
    return () => clearInterval(interval);
  }, []);
  
  // Fetch current active model on mount
  useEffect(() => {
    fetch('/api/models')
      .then(res => res.json())
      .then(data => {
        if (data.current) {
          setActiveModel(data.current);
        }
      })
      .catch(err => console.error('Failed to fetch models:', err));
  }, []);

  // Extract values safely with defaults
  const aqi = latest?.aqi ?? 0;
  const temperature = latest?.temperature ?? null;
  const humidity = latest?.humidity ?? null;
  const pressure = latest?.pressure ?? null;
  const gasResistance = latest?.gas_resistance ?? null;
  const prediction = latest?.prediction ?? {};
  const color = latest?.color ?? '#666666';
  const textColor = latest?.text_color ?? '#ffffff';
  const recommendation = latest?.recommendation ?? '';

  return (
    <>
      {/* Header */}
      <Header 
        isConnected={isConnected}
        mode={mode}
        lastUpdate={latest?.timestamp}
      />

      {/* Main Content */}
      <div className="p-4 md:p-6 max-w-7xl mx-auto space-y-6">
        
        {/* Loading state */}
        {loading && !latest && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Connecting to sensor...</p>
            </div>
          </div>
        )}

        {/* Error state */}
        {error && !latest && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center text-red-400">
              <p className="text-xl mb-2">Connection Error</p>
              <p className="text-gray-500">{error}</p>
              <p className="text-sm text-gray-600 mt-4">
                Make sure the backend is running:<br />
                <code className="bg-gray-800 px-2 py-1 rounded">python app.py --demo</code>
              </p>
            </div>
          </div>
        )}

        {/* Dashboard content - only show when we have data or no error */}
        {(latest || (!loading && !error)) && (
          <>
            {/* Alerts Panel - Always visible at top */}
            <AlertPanel />

            {/* AI Insights - Natural language summary */}
            <AIInsights latest={latest} forecast={forecast} alerts={alerts} />

            {/* Top Section: AQI Gauge + Sensor Cards */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* AQI Gauge */}
              <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6 flex items-center justify-center">
                <AqiGauge 
                  aqi={aqi}
                  label={prediction?.label ?? 'Waiting...'}
                  color={color}
                  textColor={textColor}
                />
              </div>

              {/* Sensor Cards Grid */}
              <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                <SensorCard 
                  type="temperature"
                  value={temperature}
                  color="red"
                />
                <SensorCard 
                  type="humidity"
                  value={humidity}
                  color="cyan"
                />
                <SensorCard 
                  type="pressure"
                  value={pressure}
                  color="blue"
                />
                <SensorCard 
                  type="gas"
                  value={gasResistance}
                  color="green"
                />
              </div>
            </div>

            {/* ML Section: Model Selector + Prediction */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ModelSelector 
                activeModel={activeModel}
                onSelectModel={setActiveModel}
              />
              <PredictionCard 
                prediction={prediction}
                model={latest?.model_used ?? 'rule_based'}
                inferenceTime={latest?.inference_time_ms ?? 0.1}
                confidence={prediction?.confidence}
                recommendation={recommendation}
              />
            </div>

            {/* Model Comparison Table */}
            <ModelComparison 
              activeModel={activeModel}
              onSelectModel={setActiveModel}
            />

            {/* 6-Hour Forecast */}
            <ForecastChart />

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Chart 
                data={chartData}
                dataKey="temperature"
                color="#ef4444"
                title="Temperature (24h)"
                unit="°C"
                type="area"
              />
              <Chart 
                data={chartData}
                dataKey="aqi"
                color="#22c55e"
                title="Air Quality Index (24h)"
                unit=""
                type="area"
              />
            </div>

            {/* Statistics */}
            <Stats stats={stats} />

            {/* Footer */}
            <footer className="text-center text-gray-500 text-sm pt-4 border-t border-gray-800">
              <p>
                Air Quality Monitor • React + Flask + ML
              </p>
              <p className="text-xs mt-1">
                {mode === 'demo' ? '🎮 Demo Mode' : '📡 Live'} • 
                Model: {latest?.model_used ?? 'rule_based'}
              </p>
            </footer>
          </>
        )}
      </div>
    </>
  );
}
