import { useState, useEffect } from 'react';
import { api } from '../api/client.js';

export function useSettings() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    api.getSettings()
      .then(setSettings)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const update = async (data) => {
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
