import React from 'react';


export default function AqiGauge({ aqi = 0, label = 'Unknown', color = '#666666', textColor = '#ffffff' }) {
  // Calculate stroke dash for gauge fill (0-500 AQI maps to 0-100%)
  const percentage = Math.min((aqi / 500) * 100, 100);
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  // Determine size classes
  const getAqiDescription = () => {
    if (aqi <= 50) return 'Air quality is satisfactory';
    if (aqi <= 100) return 'Acceptable air quality';
    if (aqi <= 150) return 'Sensitive groups at risk';
    if (aqi <= 200) return 'Everyone may feel effects';
    if (aqi <= 300) return 'Health alert for all';
    return 'Emergency conditions';
  };

  return (
    <div className="flex flex-col items-center">
      {/* Gauge SVG */}
      <div className="relative w-40 h-40 md:w-48 md:h-48">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="#374151"
            strokeWidth="8"
          />
          
          {/* Colored progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="gauge-circle transition-all duration-1000 ease-out"
            style={{
              filter: `drop-shadow(0 0 6px ${color}50)`,
            }}
          />
        </svg>

        {/* Center content */}
        <div 
          className="absolute inset-0 flex flex-col items-center justify-center rounded-full m-4"
          style={{ backgroundColor: `${color}20` }}
        >
          <span 
            className="text-4xl md:text-5xl font-bold"
            style={{ color: color }}
          >
            {aqi}
          </span>
          <span 
            className="text-sm md:text-base font-semibold mt-1 px-2 text-center"
            style={{ color: textColor === '#000000' ? '#1f2937' : color }}
          >
            {label}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className="text-gray-400 text-sm mt-4 text-center max-w-[200px]">
        {getAqiDescription()}
      </p>

      {/* AQI Scale Legend */}
      <div className="flex gap-1 mt-4">
        {[
          { color: '#00e400', label: 'Good' },
          { color: '#ffff00', label: 'Moderate' },
          { color: '#ff7e00', label: 'Sensitive' },
          { color: '#ff0000', label: 'Unhealthy' },
          { color: '#8f3f97', label: 'Very Unhealthy' },
        ].map((item, idx) => (
          <div 
            key={idx}
            className="w-6 h-2 rounded-sm"
            style={{ backgroundColor: item.color }}
            title={item.label}
          />
        ))}
      </div>
    </div>
  );
}
