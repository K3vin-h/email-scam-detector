import { useState, useEffect } from 'react';
import { api } from '../api/client.js';

export const DEMO_KEY = 'scamfilter_demo';
export const isDemoMode = () => localStorage.getItem(DEMO_KEY) === 'true';

export function useAuth() {
  const demo = isDemoMode();
  const [authenticated, setAuthenticated] = useState(demo ? true : null);
  const [loading, setLoading] = useState(!demo);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (demo) return;
    api.getSettings()
      .then(() => {
        setAuthenticated(true);
        setError(null);
      })
      .catch((err) => {
        // Only treat explicit auth failures as "not authenticated".
        // Network errors or 5xx should not silently log the user out.
        if (err.status === 401 || err.status === 403 || err.message === 'NOT_AUTHENTICATED') {
          setAuthenticated(false);
        } else {
          setAuthenticated(null);
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  }, [demo]);

  return { authenticated, loading, error };
}
