import React from 'react';
import { Brain, Clock, Zap, Info } from 'lucide-react';

export default function PredictionCard({ 
  prediction, 
  model = 'rule_based', 
  inferenceTime = 0.1,
  confidence = 0.85,
  recommendation = ''
}) {
  // Model display names
  const modelNames = {
    'rule_based': 'Rule-Based',
    'random_forest': 'Random Forest',
    'tsetlin': 'Tsetlin Machine',
    'xgboost': 'XGBoost',
    'neural_network': 'Neural Network',
    'decision_tree': 'Decision Tree',
    'logistic_regression': 'Logistic Regression',
  };

  const modelName = modelNames[model] || model;

  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 md:p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-purple-500/20 rounded-lg">
          <Brain className="w-6 h-6 text-purple-400" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">ML Prediction</h3>
          <p className="text-sm text-gray-400">Using {modelName}</p>
        </div>
      </div>

      {/* Prediction Result */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        {/* Prediction Label */}
        <div className="col-span-2">
          <p className="text-sm text-gray-400 mb-1">Prediction</p>
          <p className="text-2xl font-bold text-white">
            {prediction?.label || 'Waiting...'}
          </p>
        </div>

        {/* Confidence */}
        <div>
          <p className="text-sm text-gray-400 mb-1">Confidence</p>
          <p className="text-2xl font-bold text-green-400">
            {confidence ? `${(confidence * 100).toFixed(0)}%` : '--'}
          </p>
        </div>
      </div>

      {/* Metrics */}
      <div className="flex gap-4 pt-4 border-t border-gray-700">
        <div className="flex items-center gap-2 text-sm">
          <Clock className="w-4 h-4 text-gray-500" />
          <span className="text-gray-400">Inference:</span>
          <span className="text-white font-medium">{inferenceTime}ms</span>
        </div>
        
        <div className="flex items-center gap-2 text-sm">
          <Zap className="w-4 h-4 text-gray-500" />
          <span className="text-gray-400">Model:</span>
          <span className="text-white font-medium">{modelName}</span>
        </div>
      </div>

      {/* Recommendation */}
      {recommendation && (
        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
          <div className="flex gap-2">
            <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-blue-200">{recommendation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
