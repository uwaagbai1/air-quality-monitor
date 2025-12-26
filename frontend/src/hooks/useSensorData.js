import { useState, useEffect, useCallback } from 'react';
import { getLatestReading, getChartData, getStats, getHealth } from '../api/client';

/**
 * Custom hook for fetching and managing sensor data
 * @param {number} refreshInterval - Polling interval in milliseconds
 */
export function useSensorData(refreshInterval = 3000) {
  const [latest, setLatest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [mode, setMode] = useState('unknown');

  const fetchLatest = useCallback(async () => {
    try {
      const data = await getLatestReading();
      setLatest(data);
      setError(null);
      setIsConnected(true);
    } catch (err) {
      // Don't set error for 404 (no readings yet)
      if (!err.message.includes('404')) {
        setError(err.message);
      }
      setIsConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkHealth = useCallback(async () => {
    try {
      const health = await getHealth();
      setMode(health.mode);
      setIsConnected(true);
    } catch (err) {
      setIsConnected(false);
    }
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    checkHealth();
    fetchLatest();

    const interval = setInterval(fetchLatest, refreshInterval);
    const healthInterval = setInterval(checkHealth, 10000);

    return () => {
      clearInterval(interval);
      clearInterval(healthInterval);
    };
  }, [fetchLatest, checkHealth, refreshInterval]);

  return {
    latest,
    loading,
    error,
    isConnected,
    mode,
    refresh: fetchLatest,
  };
}

/**
 * Custom hook for chart data
 * @param {number} hours - Number of hours to fetch
 * @param {number} refreshInterval - Polling interval in milliseconds
 */
export function useChartData(hours = 24, refreshInterval = 60000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      const chartData = await getChartData(hours);
      setData(chartData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return { data, loading, error, refresh: fetchData };
}

/**
 * Custom hook for statistics
 * @param {number} hours - Time period in hours
 * @param {number} refreshInterval - Polling interval in milliseconds
 */
export function useStats(hours = 24, refreshInterval = 60000) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const data = await getStats(hours);
      setStats(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchStats, refreshInterval]);

  return { stats, loading, error, refresh: fetchStats };
}

export default useSensorData;
