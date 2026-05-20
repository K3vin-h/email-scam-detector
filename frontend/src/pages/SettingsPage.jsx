import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useSettings } from '../hooks/useSettings.js';

const NOTIFY_OPTIONS = [
  { value: 'daily',   label: 'Daily' },
  { value: 'weekly',  label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];

export function SettingsPage() {
  const [searchParams] = useSearchParams();
  const connected = searchParams.get('connected') === 'true';
  const { settings, loading, saving, saveError, update } = useSettings();
  const [form, setForm] = useState(null);
  const [saved, setSaved] = useState(false);
  const savedTimerRef = useRef(null);

  useEffect(() => {
    if (settings && !form) setForm({ ...settings });
  }, [settings, form]);

  if (loading || !form) {
    return <div className="py-16 text-center text-sm text-slate-400">Loading settings…</div>;
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaved(false);
    try {
      await update(form);
      setSaved(true);
      clearTimeout(savedTimerRef.current);
      savedTimerRef.current = setTimeout(() => setSaved(false), 3000);
    } catch {
      // saveError is set by the useSettings hook
    }
  };

  return (
    <div className="space-y-6 max-w-xl">
      <h1 className="text-2xl font-bold text-slate-900">Settings</h1>

      {connected && (
        <div role="status" className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700 font-medium">
          Gmail connected successfully.
        </div>
      )}
      {saved && (
        <div role="status" className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700 font-medium">
          Settings saved.
        </div>
      )}
      {saveError && (
        <div role="alert" className="rounded-lg bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
          Failed to save settings. Please try again.
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100">
        <div className="px-6 py-5">
          <label htmlFor="scan_window_days" className="block text-sm font-medium text-slate-700 mb-1">
            Scan window (days)
          </label>
          <input
            id="scan_window_days"
            type="number"
            name="scan_window_days"
            value={form.scan_window_days}
            onChange={handleChange}
            min={1}
            max={365}
            className="w-32 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <p className="mt-1 text-xs text-slate-400">How many days back to scan your inbox.</p>
        </div>

        <div className="px-6 py-5">
          <label htmlFor="scan_frequency_hours" className="block text-sm font-medium text-slate-700 mb-1">
            Scan frequency (hours)
          </label>
          <input
            id="scan_frequency_hours"
            type="number"
            name="scan_frequency_hours"
            value={form.scan_frequency_hours}
            onChange={handleChange}
            min={1}
            max={168}
            className="w-32 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <p className="mt-1 text-xs text-slate-400">How often to run automatic scans.</p>
        </div>

        <div className="px-6 py-5">
          <label htmlFor="notify_frequency" className="block text-sm font-medium text-slate-700 mb-1">
            Report frequency
          </label>
          <select
            id="notify_frequency"
            name="notify_frequency"
            value={form.notify_frequency}
            onChange={handleChange}
            className="rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            {NOTIFY_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        <div className="px-6 py-5 space-y-3">
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="notify_via_email"
              name="notify_via_email"
              checked={form.notify_via_email}
              onChange={handleChange}
              className="rounded border-slate-300 focus:ring-slate-400"
            />
            <label htmlFor="notify_via_email" className="text-sm font-medium text-slate-700">
              Email me scan summaries
            </label>
          </div>

          {form.notify_via_email && (
            <div>
              <label htmlFor="notify_email_address" className="block text-sm font-medium text-slate-700 mb-1">
                Notification email
              </label>
              <input
                id="notify_email_address"
                type="email"
                name="notify_email_address"
                value={form.notify_email_address}
                onChange={handleChange}
                placeholder="you@example.com"
                className="w-full max-w-xs rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
          )}
        </div>

        <div className="px-6 py-5">
          <button
            type="submit"
            disabled={saving}
            className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-700 disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : 'Save settings'}
          </button>
        </div>
      </form>

      <div className="bg-white rounded-xl border border-slate-200 px-6 py-5">
        <h2 className="text-sm font-semibold text-slate-700 mb-1">Gmail Integration</h2>
        <p className="text-xs text-slate-500 mb-4">
          Connect your Gmail account so the scanner can read and label your emails.
        </p>
        <a
          href="/auth/gmail/"
          className="inline-flex items-center px-4 py-2 bg-white border border-slate-200 text-sm font-medium text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
        >
          {connected ? 'Reconnect Gmail' : 'Connect Gmail'}
        </a>
      </div>
    </div>
  );
}
