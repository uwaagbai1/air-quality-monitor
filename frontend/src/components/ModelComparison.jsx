import React, { useState, useEffect } from 'react';
import { BarChart3, Zap, HardDrive, Clock, Battery, Trophy, Sparkles } from 'lucide-react';

export default function ModelComparison({ onSelectModel, activeModel }) {
  const [comparison, setComparison] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchComparison();
  }, []);

  const fetchComparison = async () => {
    try {
      const res = await fetch('/api/models/compare');
      const data = await res.json();
      setComparison(data.comparison || []);
      setError(null);
    } catch (err) {
      setError('Failed to load model comparison');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Find best values for highlighting
  const getBestValues = () => {
    if (comparison.length === 0) return {};
    
    return {
      accuracy: Math.max(...comparison.map(m => m.accuracy)),
      inference: Math.min(...comparison.map(m => m.inference_time_ms)),
      size: Math.min(...comparison.map(m => m.model_size_kb)),
      energy: Math.min(...comparison.map(m => m.energy_mj)),
      battery: Math.max(...comparison.map(m => m.battery_days)),
    };
  };

  const best = getBestValues();

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700 rounded w-1/3"></div>
          <div className="h-40 bg-gray-700 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || comparison.length === 0) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Model Comparison</h3>
        </div>
        <div className="text-center py-8 text-gray-400">
          <p>{error || 'No models trained yet'}</p>
          <p className="text-sm mt-2">Run: <code className="bg-gray-700 px-2 py-1 rounded">python ml/train_all.py</code></p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Model Comparison</h3>
        </div>
        <span className="text-xs text-gray-500">{comparison.length} models loaded</span>
      </div>

      {/* Scrollable table wrapper */}
      <div className="overflow-x-auto -mx-4 px-4">
        <table className="w-full min-w-[600px]">
          <thead>
            <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
              <th className="pb-3 font-medium">Model</th>
              <th className="pb-3 font-medium text-right">
                <div className="flex items-center justify-end gap-1">
                  <Trophy className="w-3 h-3" />
                  Accuracy
                </div>
              </th>
              <th className="pb-3 font-medium text-right">
                <div className="flex items-center justify-end gap-1">
                  <Clock className="w-3 h-3" />
                  Inference
                </div>
              </th>
              <th className="pb-3 font-medium text-right">
                <div className="flex items-center justify-end gap-1">
                  <HardDrive className="w-3 h-3" />
                  Size
                </div>
              </th>
              <th className="pb-3 font-medium text-right">
                <div className="flex items-center justify-end gap-1">
                  <Zap className="w-3 h-3" />
                  Energy
                </div>
              </th>
              <th className="pb-3 font-medium text-right">
                <div className="flex items-center justify-end gap-1">
                  <Battery className="w-3 h-3" />
                  Battery
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {comparison.map((model, idx) => {
              const isActive = model.id === activeModel;
              const isBestAccuracy = model.accuracy === best.accuracy;
              const isBestInference = model.inference_time_ms === best.inference;
              const isBestSize = model.model_size_kb === best.size;
              const isBestEnergy = model.energy_mj === best.energy;
              const isBestBattery = model.battery_days === best.battery;
              
              return (
                <tr 
                  key={model.id}
                  onClick={() => onSelectModel && onSelectModel(model.id)}
                  className={`
                    border-b border-gray-700/50 cursor-pointer transition-colors
                    ${isActive ? 'bg-blue-500/10' : 'hover:bg-gray-700/30'}
                  `}
                >
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      {model.highlight && (
                        <Sparkles className="w-4 h-4 text-purple-400" />
                      )}
                      <span className={`font-medium ${isActive ? 'text-blue-400' : 'text-white'}`}>
                        {model.name}
                      </span>
                      {isActive && (
                        <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded">
                          Active
                        </span>
                      )}
                    </div>
                  </td>
                  <td className={`py-3 text-right font-mono ${isBestAccuracy ? 'text-green-400' : 'text-gray-300'}`}>
                    {model.accuracy.toFixed(1)}%
                    {isBestAccuracy && <span className="ml-1">⚡</span>}
                  </td>
                  <td className={`py-3 text-right font-mono ${isBestInference ? 'text-green-400' : 'text-gray-300'}`}>
                    {model.inference_time_ms.toFixed(2)}ms
                    {isBestInference && <span className="ml-1">⚡</span>}
                  </td>
                  <td className={`py-3 text-right font-mono ${isBestSize ? 'text-green-400' : 'text-gray-300'}`}>
                    {model.model_size_kb < 1 
                      ? `${(model.model_size_kb * 1024).toFixed(0)}B`
                      : model.model_size_kb < 1024 
                        ? `${model.model_size_kb.toFixed(1)}KB`
                        : `${(model.model_size_kb / 1024).toFixed(1)}MB`
                    }
                    {isBestSize && <span className="ml-1">⚡</span>}
                  </td>
                  <td className={`py-3 text-right font-mono ${isBestEnergy ? 'text-green-400' : 'text-gray-300'}`}>
                    {model.energy_mj.toFixed(3)}mJ
                    {isBestEnergy && <span className="ml-1">⚡</span>}
                  </td>
                  <td className={`py-3 text-right font-mono ${isBestBattery ? 'text-green-400' : 'text-gray-300'}`}>
                    {model.battery_days.toFixed(0)}d
                    {isBestBattery && <span className="ml-1">⚡</span>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-700 text-xs text-gray-500">
        <div className="flex items-center gap-1">
          <span>⚡</span>
          <span>Best in category</span>
        </div>
        <div className="flex items-center gap-1">
          <Sparkles className="w-3 h-3 text-purple-400" />
          <span>Research highlight</span>
        </div>
        <div className="text-gray-600 ml-auto">
          Battery: 1000mAh @ 3.7V, inference every 30s
        </div>
      </div>
    </div>
  );
}
