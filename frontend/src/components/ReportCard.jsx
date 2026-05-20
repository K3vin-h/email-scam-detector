const PERIOD_LABELS = { daily: 'Daily', weekly: 'Weekly', monthly: 'Monthly' };
const PERIOD_COLORS = {
  daily:   'bg-blue-50 text-blue-700',
  weekly:  'bg-violet-50 text-violet-700',
  monthly: 'bg-amber-50 text-amber-700',
};

function formatDateTime(iso) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function ReportCard({ report }) {
  const senders = Array.isArray(report.top_senders) ? report.top_senders : [];
  const colorClass = PERIOD_COLORS[report.period] ?? 'bg-slate-100 text-slate-600';

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <div className="flex items-start gap-4">
        <div className="flex-1 min-w-0">
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
            {PERIOD_LABELS[report.period] ?? report.period}
          </span>
          <p className="mt-2 text-3xl font-bold tabular-nums text-slate-900">
            {report.total_scams}
            <span className="text-base font-normal text-slate-500 ml-1">scams</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Generated {formatDateTime(report.generated_at)}
          </p>
        </div>
      </div>

      {senders.length > 0 && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">Top Senders</p>
          <ol className="space-y-1.5">
            {senders.map((s, i) => (
              <li key={s.sender} className="flex items-center justify-between text-sm">
                <span className="text-slate-700 truncate">
                  <span className="text-slate-400 mr-2 tabular-nums">{i + 1}.</span>
                  {s.sender}
                </span>
                <span className="text-slate-500 tabular-nums ml-3 shrink-0">{s.count}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
