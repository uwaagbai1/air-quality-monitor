import React from 'react';
import { Activity, Wifi, WifiOff, Cpu } from 'lucide-react';

export default function Header({ isConnected, mode, lastUpdate }) {
  const formatTime = (timestamp) => {
    if (!timestamp) return '--:--';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <header className="bg-gray-800 border-b border-gray-700 px-4 md:px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
        {/* Logo & Title */}
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-600 rounded-lg">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-white">
              Air Quality Monitor
              <span className="text-blue-400 ml-1">Pro</span>
            </h1>
            <p className="text-xs text-gray-400 hidden sm:block">
              Real-time IoT Dashboard with ML Predictions
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center gap-4">
          {/* Mode Badge */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
            ${mode === 'demo' 
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' 
              : 'bg-green-500/20 text-green-300 border border-green-500/30'
            }`}
          >
            <Cpu className="w-4 h-4" />
            {mode === 'demo' ? 'Demo Mode' : 'Live'}
          </div>

          {/* Connection Status */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium
            ${isConnected 
              ? 'bg-green-500/20 text-green-300' 
              : 'bg-red-500/20 text-red-300'
            }`}
          >
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4" />
                <span className="hidden sm:inline">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4" />
                <span className="hidden sm:inline">Disconnected</span>
              </>
            )}
          </div>

          {/* Last Update */}
          <div className="text-gray-400 text-sm hidden md:block">
            Updated: {formatTime(lastUpdate)}
          </div>
        </div>
      </div>
    </header>
  );
}
