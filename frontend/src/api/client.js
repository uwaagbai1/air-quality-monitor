const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API call failed: ${endpoint}`, error);
    throw error;
  }
}

/**
 * Health check
 */
export async function getHealth() {
  return fetchAPI('/health');
}

/**
 * Get latest sensor reading
 */
export async function getLatestReading() {
  return fetchAPI('/latest');
}

/**
 * Get historical readings
 * @param {number} hours - Number of hours to fetch
 * @param {number} limit - Maximum number of readings
 */
export async function getReadings(hours = 24, limit = 500) {
  return fetchAPI(`/readings?hours=${hours}&limit=${limit}`);
}

/**
 * Get data formatted for charts
 * @param {number} hours - Number of hours to fetch
 */
export async function getChartData(hours = 24) {
  return fetchAPI(`/chart?hours=${hours}`);
}

/**
 * Get aggregated statistics
 * @param {number} hours - Time period in hours
 */
export async function getStats(hours = 24) {
  return fetchAPI(`/stats?hours=${hours}`);
}

/**
 * Get available ML models
 */
export async function getModels() {
  return fetchAPI('/models');
}

/**
 * Get prediction with specific model
 * @param {string} model - Model ID
 */
export async function getPrediction(model = 'rule_based') {
  return fetchAPI(`/predict?model=${model}`);
}

/**
 * Get active alerts
 */
export async function getAlerts() {
  return fetchAPI('/alerts');
}

export default {
  getHealth,
  getLatestReading,
  getReadings,
  getChartData,
  getStats,
  getModels,
  getPrediction,
  getAlerts,
};
