import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client.js';
import { isDemoMode } from './useAuth.js';
import { DEMO_REPORTS, filterReports } from '../demo/mockData.js';

export function useReports(period) {
  const demo = isDemoMode();
  const [reports, setReports] = useState(() => demo ? filterReports(DEMO_REPORTS, period) : []);
  const [count, setCount] = useState(() => demo ? filterReports(DEMO_REPORTS, period).length : 0);
  const [loading, setLoading] = useState(!demo);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (demo) {
      const filtered = filterReports(DEMO_REPORTS, period);
      setReports(filtered);
      setCount(filtered.length);
      return;
    }
    setLoading(true);
    setError(null);
    api.getReports(period)
      .then((data) => {
        setReports(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [demo, period]);

  return { reports, count, loading, error };
}
