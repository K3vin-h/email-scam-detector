import { Flame } from 'lucide-react';
import { GlassCard } from './GlassCard.jsx';

const PERIOD_BADGE = {
  daily:   'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-500/10 dark:text-amber-200 dark:border-amber-500/20',
  weekly:  'bg-violet-50 text-violet-700 border-violet-100 dark:bg-violet-500/10 dark:text-violet-200 dark:border-violet-500/20',
  monthly: 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-500/10 dark:text-indigo-200 dark:border-indigo-500/20',
};
const PERIOD_TINT = {
  daily:   'from-amber-500/10 to-amber-500/0',
  weekly:  'from-violet-500/10 to-violet-500/0',
  monthly: 'from-indigo-500/10 to-indigo-500/0',
};
const PERIOD_LABELS = { daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly' };

export function ReportCard({ report, featured = false }) {
  const senders = Array.isArray(report.top_senders) ? report.top_senders : [];
  const maxCount = senders[0]?.count || 1;
  const badgeClass = PERIOD_BADGE[report.period] ?? 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700';
  const tintClass  = PERIOD_TINT[report.period]  ?? 'from-slate-500/8 to-slate-500/0';
  const scanned    = report.total_scanned ?? report.total_count ?? null;
  const ratio      = scanned ? (report.total_scams / scanned * 100).toFixed(1) : null;

  return (
    <GlassCard hover className={`${featured ? 'p-6 md:col-span-2 ring-1 ring-rose-100/60 dark:ring-slate-700/60' : 'p-5'} relative overflow-hidden flex flex-col`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${featured ? 'from-rose-500/10 to-rose-500/0' : tintClass} pointer-events-none`} />

      {/* Header — period badge + date */}
      <div className="relative flex items-start justify-between gap-3 mb-4">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeClass}`}>
          {PERIOD_LABELS[report.period] ?? report.period}
        </span>
        <span className="text-xs text-slate-400 dark:text-slate-500 tabular-nums">
          {new Date(report.generated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>

      {/* Big scam count */}
      <div className="relative flex items-baseline gap-2 mb-1">
        <span className={`${featured ? 'text-7xl' : 'text-5xl'} font-bold tracking-tight tabular-nums text-rose-500 dark:text-rose-400`}>
          {report.total_scams}
        </span>
        <div>
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">scams detected</p>
          {scanned && (
            <p className="text-xs text-slate-400 dark:text-slate-500">
              of {scanned.toLocaleString()} scanned · <span className="font-semibold text-rose-600 dark:text-rose-400">{ratio}%</span>
            </p>
          )}
        </div>
      </div>

      {/* Sender list */}
      {senders.length > 0 && (
        <div className="relative mt-5 pt-5 border-t border-slate-200/60 dark:border-slate-700/50">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3">
            <Flame size={11} strokeWidth={2.4} className="text-rose-400" />
            Top senders
          </p>
          <ul className="space-y-2.5">
            {senders.slice(0, featured ? 5 : 4).map((s, i) => (
              <li key={s.sender} className="flex items-center gap-3">
                <span className="w-4 shrink-0 text-xs font-bold tabular-nums text-slate-400 dark:text-slate-500">
                  {i + 1}
                </span>
                <span className="flex-1 min-w-0 truncate text-xs text-slate-700 dark:text-slate-300">
                  {s.sender}
                </span>
                <div className="w-20 h-1.5 shrink-0 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-rose-400 to-rose-500"
                    style={{ width: `${(s.count / maxCount) * 100}%` }}
                  />
                </div>
                <span className="w-6 shrink-0 text-right text-xs font-semibold tabular-nums text-rose-600 dark:text-rose-400">
                  {s.count}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="relative mt-5 text-[11px] text-slate-400 dark:text-slate-500">
        Generated {new Date(report.generated_at).toLocaleString('en-US', {
          month: 'short', day: 'numeric', year: 'numeric',
          hour: '2-digit', minute: '2-digit',
        })}
      </p>
    </GlassCard>
  );
}
