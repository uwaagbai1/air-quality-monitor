import React, { useState, useEffect } from 'react';
import { Sparkles, RefreshCw, AlertTriangle, TrendingUp, TrendingDown, Minus, Thermometer } from 'lucide-react';

export default function AIInsights({ latest, forecast, alerts }) {
  const [insight, setInsight] = useState(null);
  const [loading, setLoading] = useState(false);

  // Generate insights when data changes
  useEffect(() => {
    if (latest) {
      generateInsight();
    }
  }, [latest?.aqi, alerts?.length]);

  const generateInsight = () => {
    if (!latest) return;

    setLoading(true);
    setTimeout(() => {
      const newInsight = buildInsight(latest, forecast, alerts);
      setInsight(newInsight);
      setLoading(false);
    }, 500);
  };

  const buildInsight = (data, forecastData, alertsData) => {
    const aqi = data.aqi || 0;
    const temp = data.temperature || 0;
    const humidity = data.humidity || 0;

    let category, emoji, severity;
    if (aqi <= 50) {
      category = 'Good';
      emoji = '😊';
      severity = 'good';
    } else if (aqi <= 100) {
      category = 'Moderate';
      emoji = '😐';
      severity = 'moderate';
    } else if (aqi <= 150) {
      category = 'Unhealthy for Sensitive Groups';
      emoji = '😷';
      severity = 'sensitive';
    } else if (aqi <= 200) {
      category = 'Unhealthy';
      emoji = '🤢';
      severity = 'unhealthy';
    } else if (aqi <= 300) {
      category = 'Very Unhealthy';
      emoji = '🤮';
      severity = 'very-unhealthy';
    } else {
      category = 'Hazardous';
      emoji = '☠️';
      severity = 'hazardous';
    }

    let summary = '';
    let recommendation = '';
    let trend = 'stable';
    let trendText = '';

    if (forecastData?.summary) {
      trend = forecastData.summary.trend || 'stable';
      const avgForecast = forecastData.summary.avg_aqi || aqi;

      if (trend === 'improving') {
        trendText = `Air quality is expected to improve over the next 6 hours, with average AQI dropping to ${avgForecast}.`;
      } else if (trend === 'worsening') {
        trendText = `⚠️ Air quality is expected to worsen, potentially reaching AQI ${forecastData.summary.max_aqi} in ${forecastData.summary.max_at_hours} hours.`;
      } else {
        trendText = `Conditions are expected to remain stable around AQI ${avgForecast} for the next 6 hours.`;
      }
    }

    if (aqi <= 50) {
      summary = `${emoji} Excellent air quality! The current AQI of ${aqi} indicates clean, fresh air.`;
      recommendation = 'Perfect conditions for outdoor activities and exercise.';
    } else if (aqi <= 100) {
      summary = `${emoji} Air quality is acceptable. AQI ${aqi} is moderate, though sensitive individuals may experience minor effects.`;
      recommendation = 'Most people can continue normal activities. Those with respiratory conditions should monitor how they feel.';
    } else if (aqi <= 150) {
      summary = `${emoji} Air quality is concerning for sensitive groups. At AQI ${aqi}, people with asthma or respiratory conditions may be affected.`;
      recommendation = 'Consider reducing prolonged outdoor exertion if you have respiratory conditions.';
    } else if (aqi <= 200) {
      summary = `${emoji} Air quality is unhealthy. AQI ${aqi} means everyone may begin to experience health effects.`;
      recommendation = 'Limit prolonged outdoor activities. Consider wearing a mask if going outside.';
    } else if (aqi <= 300) {
      summary = `${emoji} Very unhealthy air quality! AQI ${aqi} poses serious health risks for everyone.`;
      recommendation = 'Avoid outdoor activities. Use air purifiers indoors. Wear N95 masks if you must go outside.';
    } else {
      summary = `${emoji} HAZARDOUS air quality! AQI ${aqi} is a health emergency.`;
      recommendation = 'Stay indoors with windows sealed. Use air filtration. Seek medical attention if experiencing symptoms.';
    }

    let envContext = '';
    if (temp > 30) {
      envContext += `High temperature (${temp.toFixed(1)}°C) may worsen perceived air quality. Stay hydrated. `;
    } else if (temp < 15) {
      envContext += `Cool temperature (${temp.toFixed(1)}°C) may help with air quality perception. `;
    }

    if (humidity > 70) {
      envContext += `High humidity (${humidity.toFixed(0)}%) can trap pollutants closer to ground level.`;
    } else if (humidity < 30) {
      envContext += `Low humidity (${humidity.toFixed(0)}%) - consider using a humidifier indoors.`;
    }

    let alertContext = '';
    const activeAlerts = alertsData?.filter(a => !a.acknowledged) || [];
    if (activeAlerts.length > 0) {
      const criticalAlerts = activeAlerts.filter(a => ['critical', 'emergency'].includes(a.severity));
      if (criticalAlerts.length > 0) {
        alertContext = `🚨 ${criticalAlerts.length} critical alert${criticalAlerts.length > 1 ? 's' : ''} require${criticalAlerts.length === 1 ? 's' : ''} attention.`;
      }
    }

    return {
      summary,
      recommendation,
      trend,
      trendText,
      envContext,
      alertContext,
      severity,
      aqi,
      category,
      emoji,
      timestamp: new Date().toLocaleTimeString(),
    };
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'improving': return <TrendingDown className="w-4 h-4 text-emerald-500" />;
      case 'worsening': return <TrendingUp className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const getSeverityStyles = (severity) => {
    switch (severity) {
      case 'good': 
        return 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800';
      case 'moderate': 
        return 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800';
      case 'sensitive': 
        return 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800';
      case 'unhealthy': 
        return 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800';
      case 'very-unhealthy': 
        return 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800';
      case 'hazardous': 
        return 'bg-rose-100 dark:bg-rose-900/30 border-rose-300 dark:border-rose-800';
      default: 
        return 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700';
    }
  };

  if (!insight) {
    return (
      <div className="bg-white dark:bg-gray-800/90 border border-gray-200 dark:border-gray-700 rounded-2xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">AI Insights</h3>
        </div>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          <div className="animate-pulse">Waiting for sensor data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className={`
      border rounded-2xl p-5 transition-all
      ${getSeverityStyles(insight.severity)}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
            <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white">AI Insights</h3>
          <span className="text-2xl">{insight.emoji}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={generateInsight}
            disabled={loading}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700/50 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Summary */}
      <div className="space-y-3">
        <p className="text-gray-700 dark:text-gray-200 leading-relaxed">
          {insight.summary}
        </p>

        {/* Recommendation */}
        <div className="bg-white/50 dark:bg-gray-900/30 rounded-xl p-4">
          <p className="text-sm text-gray-700 dark:text-gray-300">
            <span className="font-semibold text-gray-900 dark:text-white">💡 Recommendation: </span>
            {insight.recommendation}
          </p>
        </div>

        {/* Trend */}
        {insight.trendText && (
          <div className="flex items-start gap-2 text-sm">
            {getTrendIcon(insight.trend)}
            <span className="text-gray-600 dark:text-gray-300">{insight.trendText}</span>
          </div>
        )}

        {/* Environmental Context */}
        {insight.envContext && (
          <div className="flex items-start gap-2 text-sm text-gray-500 dark:text-gray-400">
            <Thermometer className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{insight.envContext}</span>
          </div>
        )}

        {/* Alert Context */}
        {insight.alertContext && (
          <div className="flex items-start gap-2 text-sm text-orange-600 dark:text-orange-400">
            <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{insight.alertContext}</span>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50 text-xs text-gray-500 dark:text-gray-400">
        <span className="font-medium">AQI {insight.aqi} • {insight.category}</span>
        <span>Updated: {insight.timestamp}</span>
      </div>
    </div>
  );
}