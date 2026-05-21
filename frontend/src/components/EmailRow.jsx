import { useEffect, useRef, useState } from 'react';
import { ChevronDown } from 'lucide-react';

function formatDate(iso) {
  const date = new Date(iso);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getInitials(sender) {
  const name = (sender.split('@')[0] ?? '').replace(/[._-]/g, ' ').trim();
  return name.split(' ').map(w => w[0]?.toUpperCase() ?? '').filter(Boolean).slice(0, 2).join('') || '?';
}

const CORRECTION_OPTIONS = [
  { label: 'Legit', value: 'legit' },
  { label: 'Possible', value: 'possible_scam' },
  { label: 'Scam', value: 'scam' },
];

export function EmailRow({ email, onCorrectRisk }) {
  const [open, setOpen] = useState(false);
  const popoverRef = useRef(null);
  const pct = Math.round(email.confidence * 100);
  const riskLevel = email.risk_level ?? (email.is_scam ? 'scam' : 'legit');
  const riskLabel = email.risk_label ?? (email.is_scam ? 'Scam' : 'Legit');
  const reasons = riskLevel === 'legit'
    ? []
    : Array.isArray(email.reasons) ? email.reasons : [];
  const tone = {
    scam: {
      border: 'border-l-rose-500',
      badge: 'bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-500/20 dark:text-rose-300 dark:border-rose-500/40',
      bar:   'bg-rose-500',
      chip:  'bg-rose-100 text-rose-800 border-rose-200 dark:bg-rose-500/15 dark:text-rose-300 dark:border-rose-500/30',
    },
    possible_scam: {
      border: 'border-l-amber-500',
      badge: 'bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-500/20 dark:text-amber-300 dark:border-amber-500/40',
      bar:   'bg-amber-500',
      chip:  'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-500/15 dark:text-amber-300 dark:border-amber-500/30',
    },
    legit: {
      border: 'border-l-emerald-500',
      badge: 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-500/20 dark:text-emerald-300 dark:border-emerald-500/40',
      bar:   'bg-emerald-500',
      chip:  'bg-emerald-100 text-emerald-800 border-emerald-200 dark:bg-emerald-500/15 dark:text-emerald-300 dark:border-emerald-500/30',
    },
  }[riskLevel] ?? {
    border: 'border-l-slate-300',
    badge: 'bg-slate-100 text-slate-700 border-slate-300 dark:bg-slate-700/50 dark:text-slate-300 dark:border-slate-600',
    bar:   'bg-slate-400',
    chip:  'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-700/40 dark:text-slate-300 dark:border-slate-600/50',
  };

  useEffect(() => {
    if (!open) return undefined;
    const handlePointerDown = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) setOpen(false);
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const handleCorrection = (risk) => {
    setOpen(false);
    onCorrectRisk?.(email, risk);
  };

  return (
    <div className={`group relative flex items-start gap-3 sm:gap-4 px-4 py-3.5 border-l-4 bg-slate-50/80 backdrop-blur-sm transition-colors hover:bg-white/90 dark:bg-slate-900/55 dark:hover:bg-slate-900/80 ${open ? 'z-50' : 'z-0'} ${tone.border}`}>
      <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center mt-0.5 select-none">
        {getInitials(email.sender)}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-slate-900 truncate flex-1">{email.subject}</p>
          <div ref={popoverRef} className="relative shrink-0">
            <button
              type="button"
              onClick={() => setOpen((next) => !next)}
              aria-expanded={open}
              aria-haspopup="menu"
              aria-label={`Change risk for ${email.subject}: ${riskLabel}`}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border transition-transform active:scale-95 ${tone.badge}`}
            >
              {riskLabel}
              <ChevronDown size={11} strokeWidth={2.4} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            <div
              role="menu"
              aria-hidden={!open}
              className={`absolute right-0 top-full z-50 mt-2 w-36 origin-top-right rounded-xl border border-slate-200 bg-slate-50/95 p-1.5 shadow-xl shadow-slate-300/45 backdrop-blur-md transition-all duration-150 dark:border-slate-700 dark:bg-slate-900/95 dark:shadow-slate-950/50 ${
                open ? 'scale-100 opacity-100 translate-y-0 pointer-events-auto' : 'scale-95 opacity-0 -translate-y-1 pointer-events-none'
              }`}
            >
              {CORRECTION_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  role="menuitemradio"
                  aria-checked={riskLevel === option.value}
                  aria-label={`Mark ${email.subject} as ${option.label}`}
                  onClick={() => handleCorrection(option.value)}
                  className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-xs font-semibold transition-colors ${
                    riskLevel === option.value
                      ? 'bg-slate-700 text-white dark:bg-slate-200 dark:text-slate-900'
                      : 'text-slate-600 hover:bg-slate-200/70 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-50'
                  }`}
                >
                  {option.label}
                  {riskLevel === option.value && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                </button>
              ))}
            </div>
          </div>
          <span className="text-xs text-slate-400 tabular-nums shrink-0">{formatDate(email.received_at)}</span>
        </div>
        <p className="text-xs text-slate-500 truncate mt-1">
          <span className="font-medium text-slate-600">{email.sender}</span>
          <span className="hidden sm:inline text-slate-400"> — {email.snippet}</span>
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {reasons.map((r) => (
            <span key={r} className={`text-[10px] font-medium px-2 py-0.5 rounded-md border ${tone.chip}`}>
              {r}
            </span>
          ))}
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${tone.bar}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-[10px] tabular-nums text-slate-500">{pct}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
