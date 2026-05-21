import { useState, useEffect } from 'react';
import { api } from '../api/client.js';
import { isDemoMode } from './useAuth.js';
import { DEMO_SETTINGS } from '../demo/mockData.js';

export function useSettings() {
  const demo = isDemoMode();
  const [settings, setSettings] = useState(demo ? DEMO_SETTINGS : null);
  const [loading, setLoading] = useState(!demo);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    if (demo) return;
    api.getSettings()
      .then(setSettings)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [demo]);

  const update = async (data) => {
    if (demo) {
      const updated = { ...settings, ...data };
      setSettings(updated);
      return updated;
    }
    setSaving(true);
    setSaveError(null);
    try {
      const updated = await api.patchSettings(data);
      setSettings(updated);
      return updated;
    } catch (err) {
      setSaveError(err.message);
      throw err;
    } finally {
      setSaving(false);
    }
  };

  return { settings, loading, saving, error, saveError, update };
}
