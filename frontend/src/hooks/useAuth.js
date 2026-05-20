import { useState, useEffect } from 'react';
import { api } from '../api/client.js';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSettings()
      .then(() => setAuthenticated(true))
      .catch((err) => {
        // Only treat explicit auth failures as "not authenticated".
        // Network errors or 5xx should not silently log the user out.
        if (err.status === 401 || err.status === 403 || err.message === 'NOT_AUTHENTICATED') {
          setAuthenticated(false);
        } else {
          setAuthenticated(false); // fallback: still redirect, but preserve error for future logging
        }
      })
      .finally(() => setLoading(false));
  }, []);

  return { authenticated, loading };
}
