import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client.js';
import { isDemoMode } from './useAuth.js';
import { DEMO_STATS } from '../demo/mockData.js';

export function useStats() {
  const demo = isDemoMode();
  const [stats, setStats] = useState(demo ? DEMO_STATS : null);
  const [loading, setLoading] = useState(!demo);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const loadedRef = useRef(false);

  const fetchStats = useCallback(() => {
    if (demo) { setStats(DEMO_STATS); return; }
    if (!loadedRef.current) setLoading(true);
    else setRefreshing(true);
    setError(null);
    api.getStats()
      .then(setStats)
      .catch((err) => setError(err.message))
      .finally(() => {
        loadedRef.current = true;
        setLoading(false);
        setRefreshing(false);
      });
  }, [demo]);

  useEffect(() => {
    if (demo) return;
    fetchStats();
  }, [fetchStats, demo]);

  return { stats, loading, refreshing, error, refetch: fetchStats };
}
