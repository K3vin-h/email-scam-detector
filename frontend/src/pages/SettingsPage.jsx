import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Bell, Calendar, Check, Eye, Loader, Lock, Mail, X } from 'lucide-react';
import { useSettings } from '../hooks/useSettings.js';
import { NavBar } from '../components/NavBar.jsx';
import { MobileTabBar } from '../components/MobileTabBar.jsx';
import { PageShell } from '../components/PageShell.jsx';
import { GlassCard } from '../components/GlassCard.jsx';
import { TextInput } from '../components/TextInput.jsx';
import { Select } from '../components/Select.jsx';
import { Toggle } from '../components/Toggle.jsx';
import { NumberStepper } from '../components/NumberStepper.jsx';
import { useUnsavedChanges } from '../components/UnsavedChangesContext.jsx';

const NOTIFY_OPTIONS = [
  { value: 'daily',   label: 'Daily' },
  { value: 'weekly',  label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
];
const EDITABLE_SETTINGS_FIELDS = [
  'scan_window_days',
  'scan_frequency_hours',
  'notify_frequency',
  'notify_via_email',
  'notify_email_address',
];

function editableSettings(settings) {
  return {
    scan_window_days: Number(settings?.scan_window_days ?? 7),
    scan_frequency_hours: Number(settings?.scan_frequency_hours ?? 6),
    notify_frequency: settings?.notify_frequency ?? 'daily',
    notify_via_email: Boolean(settings?.notify_via_email),
    notify_email_address: settings?.notify_email_address ?? '',
  };
}

function SectionHeading({ label, sub }) {
  return (
    <div>
      <h2 className="text-lg font-semibold text-slate-800 tracking-tight">{label}</h2>
      {sub && <p className="text-sm text-slate-500 mt-0.5">{sub}</p>}
    </div>
  );
}

export function SettingsPage() {
  const [searchParams] = useSearchParams();
  const connectedFromRedirect = searchParams.get('connected') === 'true';
  const { settings, loading, saving, error, saveError, update } = useSettings();
  const [form, setForm] = useState(null);
  const [baseline, setBaseline] = useState(null);
  const [saved, setSaved] = useState(false);
  const [blockedPulse, setBlockedPulse] = useState(false);
  const savedTimerRef = useRef(null);
  const pulseTimerRef = useRef(null);
  const unsaved = useUnsavedChanges();
  const setUnsavedGuard = unsaved?.setGuard;

  useEffect(() => {
    if (settings && !form) {
      setForm({ ...settings });
      setBaseline(editableSettings(settings));
    }
  }, [settings, form]);

  const isDirty = !!(
    form &&
    baseline &&
    JSON.stringify(editableSettings(form)) !== JSON.stringify(baseline)
  );
  useEffect(() => {
    if (!setUnsavedGuard) return undefined;
    const pulse = () => {
      setBlockedPulse(true);
      clearTimeout(pulseTimerRef.current);
      pulseTimerRef.current = setTimeout(() => setBlockedPulse(false), 1000);
    };
    setUnsavedGuard({ active: isDirty, onBlocked: pulse });
    return () => {
      setUnsavedGuard({ active: false, onBlocked: null });
      clearTimeout(pulseTimerRef.current);
    };
  }, [isDirty, setUnsavedGuard]);

  useEffect(() => {
    const warnBeforeUnload = (event) => {
      if (!isDirty) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warnBeforeUnload);
    return () => window.removeEventListener('beforeunload', warnBeforeUnload);
  }, [isDirty]);

  if (loading) {
    return (
      <PageShell>
        <NavBar />
        <div className="flex items-center justify-center min-h-[50vh]">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Loader size={16} className="animate-spin" /> Loading settings…
          </div>
        </div>
        <MobileTabBar />
      </PageShell>
    );
  }

  if (error && !form) {
    return (
      <PageShell>
        <NavBar />
        <main className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
          <GlassCard className="p-6">
            <h1 className="text-base font-semibold text-rose-800">Settings unavailable</h1>
            <p className="mt-2 text-sm text-rose-600">Failed to load settings. Please check the backend connection.</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-white border border-rose-200 text-sm font-medium text-rose-700 rounded-lg hover:bg-rose-50 transition-colors"
            >
              Retry
            </button>
          </GlassCard>
        </main>
        <MobileTabBar />
      </PageShell>
    );
  }

  if (!form) return null;

  const handleStepperChange = (field) => (val) =>
    setForm((prev) => ({ ...prev, [field]: val }));

  const handleSelectChange = (field) => (e) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleToggle = (field) => (val) =>
    setForm((prev) => ({ ...prev, [field]: val }));

  const handleEmailChange = (e) =>
    setForm((prev) => ({ ...prev, notify_email_address: e.target.value }));

  const handleSave = async () => {
    setSaved(false);
    try {
      const updated = await update(editableSettings(form));
      setForm({ ...updated });
      setBaseline(editableSettings(updated));
      setSaved(true);
      clearTimeout(savedTimerRef.current);
      savedTimerRef.current = setTimeout(() => setSaved(false), 3000);
    } catch {
      // saveError is set by useSettings hook
    }
  };

  const handleDiscard = () => {
    if (settings) {
      setForm({ ...settings });
      setBaseline(editableSettings(settings));
    }
  };

  const isValid = !form.notify_via_email || !!form.notify_email_address;
  const gmailConnected = Boolean(form.gmail_connected || connectedFromRedirect);
  const gmailAddress = form.gmail_email_address || (gmailConnected ? 'Connected Gmail account' : 'Gmail account');
  const lastSyncLabel = form.gmail_last_sync
    ? `Last sync ${new Date(form.gmail_last_sync).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })}`
    : gmailConnected
      ? 'Last sync not available yet'
      : 'Last sync unavailable';

  return (
    <PageShell>
      <NavBar />
      <main className={`max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-7 md:pb-28 space-y-5 ${
        isDirty ? 'pb-56' : 'pb-32'
      }`}>

        <div className="mb-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-indigo-600 mb-1">Preferences</div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Settings</h1>
          <p className="text-sm text-slate-500 mt-1">Tune scan cadence, notifications, and your Gmail connection.</p>
        </div>

        {connectedFromRedirect && (
          <div role="status" className="rounded-xl bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm text-emerald-700 font-medium">
            Gmail connected successfully.
          </div>
        )}

        <GlassCard className="p-5 sm:p-6 space-y-7">
          <section>
            <div className="flex items-center gap-3 mb-5">
              <span className="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-indigo-50 text-indigo-600">
                <Calendar size={17} strokeWidth={2} />
              </span>
              <SectionHeading label="Scan Schedule" sub="Control how far back and how often the scanner runs." />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NumberStepper
                id="scan_window_days"
                label="Scan window (days)"
                helper="How many days back to scan your inbox."
                value={form.scan_window_days}
                onChange={handleStepperChange('scan_window_days')}
                min={1}
                max={365}
              />
              <NumberStepper
                id="scan_frequency_hours"
                label="Scan frequency (hours)"
                helper="How often to run automatic scans."
                value={form.scan_frequency_hours}
                onChange={handleStepperChange('scan_frequency_hours')}
                min={1}
                max={168}
              />
            </div>
          </section>

          <div className="border-t border-slate-200/70" />

          <section>
            <div className="flex items-center gap-3 mb-5">
              <span className="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-violet-50 text-violet-600">
                <Bell size={17} strokeWidth={2} />
              </span>
              <SectionHeading label="Notifications" sub="Choose when and how to receive scan summaries." />
            </div>
            <div className="space-y-4">
              <Select
                id="notify_frequency"
                label="Report frequency"
                helper="How often to generate summary reports."
                value={form.notify_frequency}
                onChange={handleSelectChange('notify_frequency')}
                options={NOTIFY_OPTIONS}
              />
              <div className="flex items-center justify-between gap-3 rounded-xl bg-white/50 border border-slate-200 px-4 py-3 dark:bg-slate-900/55 dark:border-slate-700/80">
                <div className="min-w-0">
                  <label htmlFor="notify_via_email" className="text-sm font-semibold text-slate-800">Email notifications</label>
                  <p className="text-xs text-slate-500 mt-0.5">Send report summaries to an email of your choice.</p>
                </div>
                <Toggle
                  id="notify_via_email"
                  label="Email notifications"
                  checked={form.notify_via_email}
                  onChange={handleToggle('notify_via_email')}
                  showLabel={false}
                />
              </div>
              <div className={`grid transition-all duration-300 ${form.notify_via_email ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
                <div className="overflow-hidden">
                  {form.notify_via_email && (
                    <TextInput
                      id="notify_email_address"
                      label="Notification email"
                      helper="Address to send scan summaries to."
                      type="email"
                      value={form.notify_email_address}
                      onChange={handleEmailChange}
                      placeholder="you@example.com"
                      error={!form.notify_email_address ? 'Required when email notifications are on.' : undefined}
                    />
                  )}
                </div>
              </div>
            </div>
          </section>

          <div className="border-t border-slate-200/70" />

          <section>
            <div className="flex items-center gap-3 mb-5">
              <span className="inline-flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600">
                <Mail size={17} strokeWidth={2} />
              </span>
              <SectionHeading label="Gmail Integration" sub="Connect your Gmail account so the scanner can read and label emails." />
            </div>
            <div className="rounded-xl bg-gradient-to-r from-emerald-50/80 to-white/60 border border-emerald-200/60 p-4 dark:from-emerald-950/28 dark:via-slate-900/75 dark:to-slate-900/55 dark:border-emerald-500/20">
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <span className="shrink-0 w-10 h-10 rounded-xl bg-emerald-100/80 border border-emerald-200/80 flex items-center justify-center text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/20 dark:text-emerald-300">
                  <Mail size={18} strokeWidth={2} />
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <div className="text-sm font-semibold text-slate-800 truncate">
                      {gmailAddress}
                    </div>
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      gmailConnected ? 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/25' : 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700'
                    }`}>
                      <span className={`w-1 h-1 rounded-full ${gmailConnected ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                      {gmailConnected ? 'Connected' : 'Ready'}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">{lastSyncLabel}</div>
                </div>
                <a
                  href="/auth/gmail/"
                  className="shrink-0 w-full sm:w-auto text-center px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-white/70 border border-slate-300 hover:bg-white hover:text-slate-800 transition active:scale-95 dark:bg-slate-950/60 dark:text-slate-300 dark:border-slate-700 dark:hover:bg-slate-900"
                >
                  {gmailConnected ? 'Reconnect Gmail' : 'Connect Gmail'}
                </a>
              </div>

              <div className="mt-4 pt-4 border-t border-emerald-200/50">
                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2 flex items-center gap-1.5">
                  <Lock size={10} strokeWidth={2.4} /> Permissions granted
                </div>
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-white/80 border border-slate-200 text-slate-700 dark:bg-slate-950/55 dark:border-slate-700 dark:text-slate-300">
                    <Eye size={11} strokeWidth={2.2} className="text-emerald-600" /> Read-only Gmail access
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-white/80 border border-slate-200 text-slate-700 dark:bg-slate-950/55 dark:border-slate-700 dark:text-slate-300">
                    <X size={11} strokeWidth={2.4} className="text-slate-400" /> No send, modify, or delete
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-medium bg-white/80 border border-slate-200 text-slate-700 dark:bg-slate-950/55 dark:border-slate-700 dark:text-slate-300">
                    <Lock size={11} strokeWidth={2.4} className="text-emerald-600" /> Local processing
                  </span>
                </div>
              </div>
            </div>
          </section>
        </GlassCard>

        {saveError && (
          <div role="alert" className="rounded-xl bg-rose-50 border border-rose-200 px-4 py-3 text-sm text-rose-700">
            Failed to save settings. Please try again.
          </div>
        )}
      </main>

      {saved && (
        <div role="status" className="fixed right-4 top-6 z-50 max-w-sm rounded-2xl border border-emerald-200 bg-emerald-50/95 px-4 py-3 text-sm text-emerald-800 shadow-xl shadow-emerald-900/10 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-emerald-500 text-white">
              <Check size={14} strokeWidth={3} />
            </span>
            <div>
              <p className="font-semibold">Settings saved</p>
              <p className="text-xs text-emerald-700/80">Your changes have been applied.</p>
            </div>
          </div>
        </div>
      )}

      {isDirty && (
        <div className="fixed bottom-20 md:bottom-6 inset-x-0 z-30 px-4">
          <div className={`mx-auto max-w-2xl rounded-3xl bg-white/85 backdrop-blur-md border shadow-2xl transition-colors duration-150 dark:bg-slate-950/80 ${
            blockedPulse
              ? 'border-rose-400 ring-2 ring-rose-400/70 shadow-rose-500/20'
              : 'border-slate-200/80 shadow-slate-900/10'
          }`}>
            <div className="px-4 sm:px-5 py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-slate-800">Unsaved changes</p>
                <p className="text-xs text-slate-400 mt-0.5">Your preferences will sync to the scanner on save.</p>
              </div>
              <div className="grid grid-cols-2 sm:flex items-center gap-2 shrink-0">
                <button
                  onClick={handleDiscard}
                  className="px-4 py-2 rounded-full text-sm font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-800"
                >
                  Discard
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !isValid}
                  className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-full font-semibold text-sm text-white bg-gradient-to-br from-indigo-500 to-violet-600 hover:shadow-lg hover:shadow-indigo-500/30 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? <><Loader size={14} strokeWidth={2.5} className="animate-spin" /> Saving…</> : 'Save changes'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <MobileTabBar />
    </PageShell>
  );
}
