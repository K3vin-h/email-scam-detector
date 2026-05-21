import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api/client.js';

export function useStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const loadedRef = useRef(false);

  const fetchStats = useCallback(() => {
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
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  return { stats, loading, refreshing, error, refetch: fetchStats };
}
