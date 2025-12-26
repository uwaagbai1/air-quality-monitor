import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import { 
  Wind, 
  Thermometer, 
  Droplets, 
  Activity,
  RefreshCw,
  Download,
  Cpu,
  CheckCircle,
  ExternalLink,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  Sun,
  Moon,
  Gauge,
  Sparkles,
  Zap,
  Timer,
  HardDrive,
  BatteryCharging
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { useSensorData, useChartData, useStats } from '../hooks/useSensorData';
import ForecastChart from './ForecastChart';
import AlertPanel from './AlertPanel';
import AIInsights from './AIInsights';


export default function ModernDashboard() {
  const [activeView, setActiveView] = useState('overview');
  const [timeRange, setTimeRange] = useState('24h');
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState('decision_tree');
  const [darkMode, setDarkMode] = useState(false);

  // Convert time range to hours
  const getHoursFromRange = (range) => {
    switch(range) {
      case '1h': return 1;
      case '6h': return 6;
      case '24h': return 24;
      case '7d': return 168;
      default: return 24;
    }
  };

  // Data hooks
  const { latest, loading, error, isConnected, mode } = useSensorData(3000);
  const [chartData, setChartData] = useState(null);
  const { stats } = useStats(getHoursFromRange(timeRange), 60000);

  // Fetch chart data when time range changes
  useEffect(() => {
    const fetchChartData = async () => {
      try {
        const hours = getHoursFromRange(timeRange);
        const res = await fetch(`/api/chart?hours=${hours}`);
        const data = await res.json();
        setChartData(data);
      } catch (e) {
        console.error('Failed to fetch chart data:', e);
      }
    };
    fetchChartData();
    const interval = setInterval(fetchChartData, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  // State
  const [forecast, setForecast] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [animateCards, setAnimateCards] = useState(false);

  // Trigger animations on mount
  useEffect(() => {
    const timer = setTimeout(() => setAnimateCards(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Apply dark mode to document root for Tailwind
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Initialize dark mode from system preference
  useEffect(() => {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(prefersDark);
  }, []);

  // Fetch forecast
  useEffect(() => {
    const fetchForecast = async () => {
      try {
        const res = await fetch('/api/forecast');
        const data = await res.json();
        if (!data.error) setForecast(data);
      } catch (e) {}
    };
    fetchForecast();
    const interval = setInterval(fetchForecast, 60000);
    return () => clearInterval(interval);
  }, []);

  // Fetch alerts
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch('/api/alerts/active');
        const data = await res.json();
        setAlerts(data.alerts || []);
      } catch (e) {}
    };
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, []);

  // Fetch models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const res = await fetch('/api/models/compare');
        const data = await res.json();
        if (data.comparison) setModels(data.comparison);
        else if (data.models) setModels(data.models);
        else if (Array.isArray(data)) setModels(data);
        
        const modelsRes = await fetch('/api/models');
        const modelsData = await modelsRes.json();
        if (modelsData.current) setActiveModel(modelsData.current);
      } catch (e) {
        console.error('Failed to fetch models:', e);
      }
    };
    fetchModels();
    const interval = setInterval(fetchModels, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle model switch
  const handleModelSwitch = async (modelId) => {
    try {
      const res = await fetch('/api/models/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      });
      const data = await res.json();
      if (data.success) {
        setActiveModel(modelId);
        // Optionally refresh data with new model
      }
    } catch (e) {
      console.error('Failed to switch model:', e);
    }
  };

  // Get AQI info
  const getAqiInfo = (aqi) => {
    if (!aqi) return { label: 'Loading...', color: '#6b7280', bg: 'from-gray-400 to-gray-500', emoji: '⏳', ring: 'ring-gray-400' };
    if (aqi <= 50) return { label: 'Good', color: '#10b981', bg: 'from-emerald-400 to-green-500', emoji: '😊', ring: 'ring-emerald-400' };
    if (aqi <= 100) return { label: 'Moderate', color: '#f59e0b', bg: 'from-amber-400 to-yellow-500', emoji: '😐', ring: 'ring-amber-400' };
    if (aqi <= 150) return { label: 'Unhealthy (Sensitive)', color: '#f97316', bg: 'from-orange-400 to-orange-500', emoji: '😷', ring: 'ring-orange-400' };
    if (aqi <= 200) return { label: 'Unhealthy', color: '#ef4444', bg: 'from-red-400 to-red-500', emoji: '🤢', ring: 'ring-red-400' };
    if (aqi <= 300) return { label: 'Very Unhealthy', color: '#8b5cf6', bg: 'from-purple-400 to-purple-500', emoji: '😨', ring: 'ring-purple-400' };
    return { label: 'Hazardous', color: '#7c2d12', bg: 'from-rose-600 to-red-700', emoji: '☠️', ring: 'ring-rose-600' };
  };

  const aqiInfo = getAqiInfo(latest?.aqi);

  // Circular AQI Gauge
  const AqiGauge = ({ value, max = 500 }) => {
    const percentage = Math.min((value || 0) / max * 100, 100);
    const circumference = 2 * Math.PI * 70;
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    
    return (
      <div className="relative w-44 h-44 mx-auto">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          <circle
            cx="80" cy="80" r="70"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-gray-200 dark:text-gray-700"
          />
          <circle
            cx="80" cy="80" r="70"
            fill="none"
            stroke={aqiInfo.color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-1000 ease-out"
            style={{ filter: `drop-shadow(0 0 10px ${aqiInfo.color}50)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-black" style={{ color: aqiInfo.color }}>
            {value || '--'}
          </span>
          <span className="text-xs text-gray-500 dark:text-gray-400 font-semibold uppercase tracking-wide">AQI</span>
          <span className="text-2xl mt-1">{aqiInfo.emoji}</span>
        </div>
      </div>
    );
  };

  // Stat Card
  const StatCard = ({ title, value, unit, icon: Icon, gradient, trend, delay = 0 }) => (
    <div 
      className={`
        relative overflow-hidden rounded-2xl p-5
        bg-white dark:bg-gray-800/90 
        border border-gray-100 dark:border-gray-700/50
        shadow-sm hover:shadow-xl dark:shadow-none
        transform transition-all duration-500 ease-out hover:-translate-y-1
        ${animateCards ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}
      `}
      style={{ transitionDelay: `${delay}ms` }}
    >
      <div className={`absolute -top-12 -right-12 w-32 h-32 rounded-full bg-gradient-to-br ${gradient} opacity-10 blur-2xl`} />
      
      <div className="relative">
        <div className="flex items-center justify-between mb-3">
          <div className={`p-2.5 rounded-xl bg-gradient-to-br ${gradient} shadow-lg`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          {trend !== undefined && (
            <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${
              trend >= 0 ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400' 
                        : 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400'
            }`}>
              {trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {Math.abs(trend)}%
            </div>
          )}
        </div>
        
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
        <div className="flex items-baseline gap-1.5 mt-1">
          <span className="text-3xl font-black text-gray-900 dark:text-white tracking-tight">
            {value !== null && value !== undefined ? value : '--'}
          </span>
          {unit && <span className="text-sm font-medium text-gray-400 dark:text-gray-500">{unit}</span>}
        </div>
      </div>
    </div>
  );

  // Model Card
  const ModelCard = ({ model, isActive, onSelect }) => {
    const accuracy = model.accuracy ? (model.accuracy > 1 ? model.accuracy : model.accuracy * 100) : null;
    
    const modelMeta = {
      'decision_tree': { icon: '🌳', color: 'emerald' },
      'random_forest': { icon: '🌲', color: 'green' },
      'xgboost': { icon: '🚀', color: 'blue' },
      'logistic_regression': { icon: '📈', color: 'purple' },
      'neural_network': { icon: '🧠', color: 'pink' },
      'tsetlin': { icon: '⚡', color: 'amber' }
    };
    
    const meta = modelMeta[model.id] || { icon: '🤖', color: 'gray' };
    
    return (
      <div 
        onClick={() => onSelect(model.id)}
        className={`
          group relative p-5 rounded-2xl cursor-pointer transition-all duration-300
          ${isActive 
            ? 'bg-gradient-to-br from-emerald-500 to-green-600 text-white shadow-xl shadow-emerald-500/30 ring-4 ring-emerald-400/30' 
            : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-750 border border-gray-200 dark:border-gray-700 hover:border-emerald-300 dark:hover:border-emerald-600'
          }
        `}
      >
        {isActive && (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 px-2.5 py-1 bg-white/20 backdrop-blur-sm rounded-full">
            <CheckCircle className="w-4 h-4" />
            <span className="text-xs font-bold">Active</span>
          </div>
        )}
        
        <div className="flex items-center gap-4 mb-4">
          <span className="text-4xl">{meta.icon}</span>
          <div>
            <h4 className={`text-lg font-bold ${isActive ? 'text-white' : 'text-gray-900 dark:text-white'}`}>
              {model.name}
            </h4>
            <p className={`text-sm ${isActive ? 'text-emerald-100' : 'text-gray-500 dark:text-gray-400'}`}>
              Click to activate
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'Accuracy', value: accuracy ? `${accuracy.toFixed(1)}%` : 'N/A', icon: Sparkles },
            { label: 'Speed', value: model.inference_time_ms ? `${model.inference_time_ms.toFixed(1)}ms` : 'N/A', icon: Zap },
            { label: 'Size', value: model.model_size_kb ? `${model.model_size_kb.toFixed(0)}KB` : 'N/A', icon: HardDrive },
            { label: 'Battery', value: model.battery_days ? `${model.battery_days.toFixed(0)}d` : 'N/A', icon: BatteryCharging }
          ].map((stat, i) => (
            <div key={i} className={`flex items-center gap-2 p-2.5 rounded-xl ${
              isActive ? 'bg-white/15' : 'bg-gray-50 dark:bg-gray-700/50'
            }`}>
              <stat.icon className={`w-4 h-4 ${isActive ? 'text-emerald-200' : 'text-gray-400'}`} />
              <div>
                <p className={`text-xs ${isActive ? 'text-emerald-200' : 'text-gray-500 dark:text-gray-400'}`}>{stat.label}</p>
                <p className={`text-sm font-bold ${isActive ? 'text-white' : 'text-gray-900 dark:text-white'}`}>{stat.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Loading state
  if (loading && !latest) {
    return (
      <div className={`flex min-h-screen items-center justify-center ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-4 border-gray-200 dark:border-gray-700" />
            <div className="absolute inset-0 rounded-full border-4 border-t-emerald-500 animate-spin" />
            <Wind className="absolute inset-0 m-auto w-10 h-10 text-emerald-500 animate-pulse" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Connecting to Sensors</h3>
          <p className="text-gray-500 dark:text-gray-400">Please wait while we establish connection...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !latest) {
    return (
      <div className={`flex min-h-screen items-center justify-center p-4 ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-3xl shadow-2xl p-8 text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
            <AlertTriangle className="w-10 h-10 text-red-500" />
          </div>
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">Connection Failed</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">{error}</p>
          <div className="bg-gray-900 dark:bg-black rounded-xl p-4 mb-6 text-left">
            <p className="text-gray-400 text-sm mb-2">Run the backend server:</p>
            <code className="text-emerald-400 font-mono">python app.py --demo</code>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="w-full py-3 bg-gradient-to-r from-emerald-500 to-green-600 text-white font-bold rounded-xl hover:from-emerald-600 hover:to-green-700 transition-all shadow-lg"
          >
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`flex min-h-screen ${darkMode ? 'dark' : ''}`}>
      {/* Animated Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800 transition-colors duration-500" />
      <div className="fixed inset-0 opacity-30 dark:opacity-20" style={{
        backgroundImage: `radial-gradient(circle at 1px 1px, rgb(148 163 184 / 0.3) 1px, transparent 0)`,
        backgroundSize: '40px 40px'
      }} />
      
      <Sidebar activeView={activeView} setActiveView={setActiveView} alertCount={alerts.length} />

      <main className="flex-1 overflow-auto relative">
        {/* Header */}
        <header className="sticky top-0 z-20 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50">
          <div className="px-4 md:px-6 py-4">
            <div className="flex items-center justify-between gap-4">
              <div className="ml-12 lg:ml-0">
                <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">
                  Dashboard / <span className="text-gray-900 dark:text-white capitalize">{activeView}</span>
                </p>
                <h1 className="text-2xl font-black text-gray-900 dark:text-white tracking-tight">
                  Air Quality Monitor
                </h1>
              </div>
              
              <div className="flex items-center gap-2 sm:gap-3">
                <div className={`hidden sm:flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${
                  isConnected 
                    ? 'bg-emerald-100 dark:bg-emerald-900/40 text-emerald-700 dark:text-emerald-400' 
                    : 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400'
                }`}>
                  <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                  {isConnected ? 'Live' : 'Offline'}
                </div>

                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className="p-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  title="Toggle dark mode"
                >
                  {darkMode ? <Sun className="w-5 h-5 text-amber-500" /> : <Moon className="w-5 h-5 text-slate-600" />}
                </button>

                <button className="hidden md:flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <Download className="w-4 h-4" />
                  Export
                </button>

                <button 
                  onClick={() => window.location.reload()}
                  className="flex items-center gap-2 px-4 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-emerald-500 to-green-600 rounded-xl hover:from-emerald-600 hover:to-green-700 transition-all shadow-lg shadow-emerald-500/25"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span className="hidden sm:inline">Refresh</span>
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-4 md:p-6 relative">
          {/* Overview View */}
          {(activeView === 'overview' || activeView === 'home' || activeView === 'dashboard' || activeView === 'analytics') && (
            <div className="space-y-6">
              <AlertPanel />
              <AIInsights latest={latest} forecast={forecast} alerts={alerts} />

              {/* Main Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* AQI Card */}
                <div className={`
                  bg-white dark:bg-gray-800/90 rounded-3xl p-6
                  border border-gray-100 dark:border-gray-700/50
                  shadow-sm
                  transform transition-all duration-500 ${animateCards ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}
                `}>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-bold text-gray-900 dark:text-white">Air Quality</h3>
                    <span className={`px-3 py-1.5 rounded-full text-sm font-bold bg-gradient-to-r ${aqiInfo.bg} text-white shadow-lg`}>
                      {aqiInfo.label}
                    </span>
                  </div>
                  <AqiGauge value={latest?.aqi} />
                  <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-4 leading-relaxed">
                    {latest?.recommendation || 'Monitoring air quality in real-time...'}
                  </p>
                </div>

                {/* Stats Grid */}
                <div className="lg:col-span-2 grid grid-cols-2 gap-4">
                  <StatCard
                    title="Temperature"
                    value={latest?.temperature?.toFixed(1)}
                    unit="°C"
                    icon={Thermometer}
                    gradient="from-orange-500 to-red-500"
                    trend={2.4}
                    delay={100}
                  />
                  <StatCard
                    title="Humidity"
                    value={latest?.humidity?.toFixed(1)}
                    unit="%"
                    icon={Droplets}
                    gradient="from-blue-500 to-cyan-500"
                    trend={-1.2}
                    delay={200}
                  />
                  <StatCard
                    title="Pressure"
                    value={latest?.pressure?.toFixed(0)}
                    unit="hPa"
                    icon={Gauge}
                    gradient="from-violet-500 to-purple-500"
                    trend={0.5}
                    delay={300}
                  />
                  <StatCard
                    title="Readings"
                    value={stats?.reading_count || stats?.count || '--'}
                    unit="today"
                    icon={Activity}
                    gradient="from-emerald-500 to-green-500"
                    trend={6.2}
                    delay={400}
                  />
                </div>
              </div>

              {/* Chart */}
              <div className={`
                bg-white dark:bg-gray-800/90 rounded-3xl p-6
                border border-gray-100 dark:border-gray-700/50
                shadow-sm
                transform transition-all duration-500 delay-500 ${animateCards ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}
              `}>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">AQI Trend</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Real-time air quality monitoring</p>
                  </div>
                  <div className="flex gap-1 p-1 bg-gray-100 dark:bg-gray-700/50 rounded-xl">
                    {['1h', '6h', '24h', '7d'].map((range) => (
                      <button
                        key={range}
                        onClick={() => setTimeRange(range)}
                        className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all ${
                          timeRange === range 
                            ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
                            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
                        }`}
                      >
                        {range}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={
                      // Transform chart data format
                      chartData?.labels?.length > 0
                        ? chartData.labels.map((label, i) => ({
                            timestamp: label,
                            aqi: chartData.aqi?.[i] || 0,
                            temperature: chartData.temperature?.[i],
                            humidity: chartData.humidity?.[i]
                          })).slice(-100)
                        : Array.isArray(chartData) 
                          ? chartData.slice(-100) 
                          : []
                    }>
                      <defs>
                        <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#10b981" stopOpacity={0.4}/>
                          <stop offset="100%" stopColor="#10b981" stopOpacity={0.05}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" className="dark:opacity-10" />
                      <XAxis 
                        dataKey="timestamp" 
                        tickFormatter={(val) => {
                          try { return new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
                          catch { return ''; }
                        }}
                        stroke="#9ca3af"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                      />
                      <YAxis stroke="#9ca3af" fontSize={12} tickLine={false} axisLine={false} />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255,255,255,0.98)', 
                          border: 'none',
                          borderRadius: '16px',
                          boxShadow: '0 20px 40px rgba(0,0,0,0.15)'
                        }}
                        labelFormatter={(val) => { try { return new Date(val).toLocaleString(); } catch { return val; }}}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="aqi" 
                        stroke="#10b981" 
                        strokeWidth={3}
                        fill="url(#aqiGradient)"
                        dot={false}
                        activeDot={{ r: 8, fill: '#10b981', stroke: '#fff', strokeWidth: 3 }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100 dark:border-gray-700">
                  {[
                    { label: 'Average', value: stats?.aqi?.avg?.toFixed(0) || stats?.avg_aqi?.toFixed(0) || '--', color: 'text-gray-900 dark:text-white' },
                    { label: 'Minimum', value: stats?.aqi?.min || stats?.min_aqi || '--', color: 'text-emerald-500' },
                    { label: 'Maximum', value: stats?.aqi?.max || stats?.max_aqi || '--', color: 'text-red-500' }
                  ].map((stat, i) => (
                    <div key={i} className="text-center">
                      <p className={`text-3xl font-black ${stat.color}`}>{stat.value}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">{stat.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              <ForecastChart />

              {/* ML Models */}
              <div className={`
                bg-white dark:bg-gray-800/90 rounded-3xl p-6
                border border-gray-100 dark:border-gray-700/50
                shadow-sm
                transform transition-all duration-500 delay-700 ${animateCards ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'}
              `}>
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">ML Models</h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{models.length} models • Click to switch</p>
                  </div>
                  <button
                    onClick={() => setActiveView('models')}
                    className="flex items-center gap-2 text-emerald-600 hover:text-emerald-700 font-semibold text-sm"
                  >
                    View all <ExternalLink className="w-4 h-4" />
                  </button>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                  {models.slice(0, 6).map((model) => (
                    <ModelCard
                      key={model.id}
                      model={model}
                      isActive={model.id === activeModel}
                      onSelect={handleModelSwitch}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Forecast View */}
          {activeView === 'forecast' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800/90 rounded-3xl p-6 border border-gray-100 dark:border-gray-700/50">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">6-Hour Forecast</h2>
                <p className="text-gray-500 dark:text-gray-400">LSTM neural network predictions based on historical patterns</p>
              </div>
              <ForecastChart />
            </div>
          )}

          {/* Models View */}
          {activeView === 'models' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800/90 rounded-3xl p-6 border border-gray-100 dark:border-gray-700/50">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Machine Learning Models</h2>
                <p className="text-gray-500 dark:text-gray-400">Compare 6 different ML approaches for air quality classification</p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {models.map((model) => (
                  <ModelCard
                    key={model.id}
                    model={model}
                    isActive={model.id === activeModel}
                    onSelect={handleModelSwitch}
                  />
                ))}
              </div>

              <div className="bg-gradient-to-br from-emerald-50 to-cyan-50 dark:from-emerald-900/20 dark:to-cyan-900/20 rounded-3xl p-6 border border-emerald-200/50 dark:border-emerald-700/30">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">📊 Selection Guide</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { icon: '🎯', title: 'Maximum Accuracy', desc: 'Random Forest / XGBoost (99.8-100%)' },
                    { icon: '⚡', title: 'Fastest Inference', desc: 'Decision Tree (0.3ms)' },
                    { icon: '🔋', title: 'Longest Battery', desc: 'Decision Tree (1540 days)' },
                    { icon: '🎓', title: 'MSc Research', desc: 'Tsetlin Machine (FPGA-ready)' }
                  ].map((item, i) => (
                    <div key={i} className="flex gap-3">
                      <span className="text-2xl">{item.icon}</span>
                      <div>
                        <p className="font-bold text-gray-900 dark:text-white">{item.title}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Alerts View */}
          {activeView === 'alerts' && (
            <div className="space-y-6">
              <div className="bg-white dark:bg-gray-800/90 rounded-3xl p-6 border border-gray-100 dark:border-gray-700/50">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Notifications & Alerts</h2>
                <p className="text-gray-500 dark:text-gray-400">Real-time monitoring with intelligent alerting</p>
              </div>
              <AlertPanel />
            </div>
          )}

          {/* Footer */}
          <footer className="text-center py-8 mt-8 border-t border-gray-200 dark:border-gray-700/50">
            <p className="text-gray-900 dark:text-white font-bold">Air Quality Monitor</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              React + Flask + TensorFlow • {mode === 'demo' ? '🎮 Demo' : '📡 Live'} • Model: {activeModel}
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              MSc Embedded Systems & IoT • Newcastle University • 2025
            </p>
          </footer>
        </div>
      </main>
    </div>
  );
}