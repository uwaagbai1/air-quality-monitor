import React, { useState, useEffect } from 'react';
import { Brain, Lock, Sparkles, Check } from 'lucide-react';

export default function ModelSelector({ activeModel, onSelectModel }) {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(null);

  useEffect(() => {
    fetchModels();
  }, []);

  const fetchModels = async () => {
    try {
      const res = await fetch('/api/models');
      const data = await res.json();
      setModels(data.models || []);
    } catch (err) {
      console.error('Failed to fetch models:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectModel = async (modelId) => {
    if (switching) return;
    
    setSwitching(modelId);
    
    try {
      const res = await fetch('/api/models/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId }),
      });
      
      if (res.ok) {
        onSelectModel && onSelectModel(modelId);
      }
    } catch (err) {
      console.error('Failed to switch model:', err);
    } finally {
      setSwitching(null);
    }
  };

  // Icons for each model
  const modelIcons = {
    'random_forest': '🌲',
    'tsetlin': '⚡',
    'xgboost': '🚀',
    'neural_network': '🧠',
    'decision_tree': '🌳',
    'logistic_regression': '📊',
    'rule_based': '📏',
  };

  if (loading) {
    return (
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/3 mb-4"></div>
          <div className="flex gap-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-10 w-24 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const loadedModels = models.filter(m => m.loaded);
  const unloadedModels = models.filter(m => !m.loaded);

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-semibold text-white">Select Model</h3>
        </div>
        <span className="text-xs text-gray-500">
          {loadedModels.length} loaded
        </span>
      </div>

      {/* Loaded Models - Clickable */}
      <div className="flex flex-wrap gap-2 mb-3">
        {loadedModels.map((model) => {
          const isActive = activeModel === model.id;
          const isSwitching = switching === model.id;

          return (
            <button
              key={model.id}
              onClick={() => handleSelectModel(model.id)}
              disabled={isSwitching}
              className={`
                relative flex items-center gap-2 px-4 py-2 rounded-lg font-medium
                transition-all duration-200
                ${isActive 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' 
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }
                ${model.highlight && !isActive ? 'ring-1 ring-purple-500/50' : ''}
                ${isSwitching ? 'opacity-50' : ''}
              `}
            >
              <span>{modelIcons[model.id] || '🤖'}</span>
              <span className="hidden sm:inline">{model.name}</span>
              
              {isActive && (
                <Check className="w-4 h-4 ml-1" />
              )}
              
              {model.highlight && !isActive && (
                <span className="absolute -top-1 -right-1">
                  <Sparkles className="w-3 h-3 text-purple-400" />
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Unloaded Models - Disabled */}
      {unloadedModels.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {unloadedModels.map((model) => (
            <button
              key={model.id}
              disabled
              className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium
                bg-gray-800 text-gray-500 cursor-not-allowed"
              title="Not trained - run train_all.py"
            >
              <span>{modelIcons[model.id] || '🤖'}</span>
              <span className="hidden sm:inline">{model.name}</span>
              <Lock className="w-3 h-3 ml-1 text-gray-600" />
            </button>
          ))}
        </div>
      )}

      {/* Help text */}
      {loadedModels.length === 0 && (
        <p className="text-xs text-gray-500 mt-3">
          💡 No models loaded. Run: <code className="bg-gray-700 px-1 rounded">python ml/train_all.py</code>
        </p>
      )}
    </div>
  );
}
