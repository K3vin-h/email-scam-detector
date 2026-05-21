import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client.js';

export function useReports(period) {
  const [reports, setReports] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchReports = useCallback(() => {
    setLoading(true);
    setError(null);
    api.getReports(period)
      .then((data) => {
        setReports(data.results);
        setCount(data.count);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [period]);

  useEffect(() => { fetchReports(); }, [fetchReports]);

  return { reports, count, loading, error };
}
