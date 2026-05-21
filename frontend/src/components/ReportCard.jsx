import { GlassCard } from './GlassCard.jsx';

const PERIOD_BADGE = {
  daily:   'bg-amber-50 text-amber-700 border-amber-200',
  weekly:  'bg-violet-50 text-violet-700 border-violet-100',
  monthly: 'bg-indigo-50 text-indigo-700 border-indigo-200',
};
const PERIOD_TINT = {
  daily: 'from-amber-500/12 to-amber-500/0',
  weekly: 'from-violet-500/12 to-violet-500/0',
  monthly: 'from-indigo-500/12 to-indigo-500/0',
};
const PERIOD_LABELS = { daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly' };

function formatDateTime(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function ReportCard({ report, featured = false }) {
  const senders = Array.isArray(report.top_senders) ? report.top_senders : [];
  const maxCount = senders[0]?.count || 1;
  const badgeClass = PERIOD_BADGE[report.period] ?? 'bg-slate-100 text-slate-600 border-slate-200';
  const tintClass = PERIOD_TINT[report.period] ?? 'from-slate-500/10 to-slate-500/0';
  const scanned = report.total_scanned ?? report.total_count ?? null;
  const ratio = scanned ? (report.total_scams / scanned * 100).toFixed(1) : null;

  return (
    <GlassCard hover className={`${featured ? 'p-6 md:col-span-2 ring-1 ring-rose-100/60' : 'p-5'} relative overflow-hidden flex flex-col`}>
      <div className={`absolute inset-0 bg-gradient-to-br ${featured ? 'from-rose-500/12 to-rose-500/0' : tintClass} pointer-events-none`} />
      <div className="relative mb-3 flex items-start justify-between gap-3">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeClass}`}>
          {PERIOD_LABELS[report.period] ?? report.period}
        </span>
        <span className="text-xs text-slate-400 tabular-nums">
          {new Date(report.generated_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
        </span>
      </div>

      <div className="relative mb-1 flex items-baseline gap-3">
        <span className={`${featured ? 'text-7xl' : 'text-5xl'} font-bold text-rose-500 tracking-tight tabular-nums`}>{report.total_scams}</span>
        <div>
          <p className="text-sm font-medium text-slate-700">scams detected</p>
          {scanned && (
            <p className="text-xs text-slate-400">
              of {scanned.toLocaleString()} scanned · <span className="font-semibold text-rose-600">{ratio}%</span>
            </p>
          )}
        </div>
      </div>

      {senders.length > 0 && (
        <div className="relative border-t border-slate-200/70 pt-4 mt-4">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Top Senders</p>
          <ol className="space-y-2.5">
            {senders.map((s, i) => (
              <li key={s.sender}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-600 truncate flex-1 mr-2">
                    <span className="text-slate-400 tabular-nums mr-1.5">{i + 1}.</span>
                    {s.sender}
                  </span>
                  <span className="text-slate-500 tabular-nums shrink-0">{s.count}</span>
                </div>
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-rose-400 to-rose-500 rounded-full transition-all"
                    style={{ width: `${(s.count / maxCount) * 100}%` }}
                  />
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      <p className="relative text-[11px] text-slate-400 mt-4">Generated {formatDateTime(report.generated_at)}</p>
    </GlassCard>
  );
}
