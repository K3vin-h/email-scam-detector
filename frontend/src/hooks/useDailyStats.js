import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client.js';
import { isDemoMode } from './useAuth.js';
import { DEMO_DAILY_STATS } from '../demo/mockData.js';

export function useDailyStats() {
  const demo = isDemoMode();
  const [data, setData] = useState(demo ? DEMO_DAILY_STATS : []);
  const [loading, setLoading] = useState(!demo);
  const [error, setError] = useState(null);

  const fetch = useCallback(() => {
    if (demo) return;
    setLoading(true);
    setError(null);
    api.getDailyStats()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [demo]);

  useEffect(() => { fetch(); }, [fetch]);

  return { data, loading, error };
}
