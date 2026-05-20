import { useState } from 'react';
import { useReports } from '../hooks/useReports.js';
import { ReportCard } from '../components/ReportCard.jsx';

const PERIOD_OPTIONS = [
  { label: 'All',     value: '' },
  { label: 'Daily',   value: 'daily' },
  { label: 'Weekly',  value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
];

export function ReportsPage() {
  const [period, setPeriod] = useState('');
  const { reports, loading, error } = useReports(period);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-2xl font-bold text-slate-900">Reports</h1>
        <div role="group" aria-label="Report period filter" className="flex gap-1 p-1 bg-slate-100 rounded-lg">
          {PERIOD_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPeriod(opt.value)}
              aria-pressed={period === opt.value}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                period === opt.value
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="py-16 text-center text-sm text-slate-400">Loading…</div>
      )}
      {error && (
        <div className="py-4 text-center text-sm text-rose-600">Failed to load reports.</div>
      )}
      {!loading && !error && reports.length === 0 && (
        <div className="py-16 text-center text-sm text-slate-400">No reports found.</div>
      )}
      {!loading && !error && reports.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2">
          {reports.map((report, i) => (
            <ReportCard key={`${report.period}-${report.generated_at}-${i}`} report={report} />
          ))}
        </div>
      )}
    </div>
  );
}
