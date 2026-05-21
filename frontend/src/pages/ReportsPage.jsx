import { useState } from 'react';
import { ShieldAlert, FileSearch, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import { useReports } from '../hooks/useReports.js';
import { useStats } from '../hooks/useStats.js';
import { useDailyStats } from '../hooks/useDailyStats.js';
import { useSenderStats } from '../hooks/useSenderStats.js';
import { NavBar } from '../components/NavBar.jsx';
import { MobileTabBar } from '../components/MobileTabBar.jsx';
import { PageShell } from '../components/PageShell.jsx';
import { GlassCard } from '../components/GlassCard.jsx';
import { ReportCard } from '../components/ReportCard.jsx';
import { KpiTile } from '../components/KpiTile.jsx';
import { FilterBar } from '../components/FilterBar.jsx';

const PERIOD_OPTIONS = [
  { label: 'All',     value: '' },
  { label: 'Daily',   value: 'daily' },
  { label: 'Weekly',  value: 'weekly' },
  { label: 'Monthly', value: 'monthly' },
];

function ReportsOverview({ data, loading }) {
  if (loading || !data.length) return null;
  const maxScanned = Math.max(...data.map(d => d.scanned), 1);
  const totalScanned = data.reduce((sum, day) => sum + day.scanned, 0);
  const totalScams = data.reduce((sum, day) => sum + day.scams, 0);

  return (
    <GlassCard className="p-5 sm:p-6">
      <div className="flex items-end justify-between flex-wrap gap-3 mb-5">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-violet-600 mb-1">Last 7 days</div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Detections over time</h2>
          <p className="text-sm text-slate-500 mt-1">Daily scans and confirmed scams.</p>
        </div>
        <div className="flex items-center gap-5">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Scanned</div>
            <div className="text-2xl font-bold tabular-nums text-slate-900">{totalScanned.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Scams</div>
            <div className="text-2xl font-bold tabular-nums text-rose-600">{totalScams.toLocaleString()}</div>
          </div>
        </div>
      </div>
      <div className="relative flex items-end gap-2 h-36 sm:h-44 rounded-xl border border-slate-200/70 bg-white/35 px-3 pt-4 pb-2 dark:border-slate-700/70 dark:bg-slate-950/25">
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none">
          {[0, 1, 2, 3].map((i) => <div key={i} className="border-t border-slate-200/60 dark:border-slate-800/90" />)}
        </div>
        {data.map((d) => {
          const scannedH = Math.round((d.scanned / maxScanned) * 100);
          const scamH = d.scanned > 0 ? Math.round((d.scams / d.scanned) * scannedH) : 0;
          return (
            <div key={d.date} className="group relative z-10 flex-1 h-full flex flex-col justify-end gap-1 min-w-0">
              <div className="absolute -top-1 left-1/2 -translate-x-1/2 -translate-y-full opacity-0 group-hover:opacity-100 transition pointer-events-none z-10">
                <div className="bg-slate-900 text-white text-[10px] font-medium px-2 py-1 rounded-md whitespace-nowrap shadow-lg dark:bg-slate-800 dark:text-slate-100 dark:border dark:border-slate-700">
                  {d.day}: <span className="text-rose-300 dark:text-rose-300">{d.scams}</span> / {d.scanned}
                </div>
              </div>
              <div className="relative mx-auto w-full max-w-8 overflow-hidden rounded-t-lg rounded-b-sm bg-gradient-to-t from-slate-200 to-slate-300/80 shadow-inner shadow-white/50 transition-all group-hover:from-slate-300 group-hover:to-slate-400/80 dark:from-slate-800 dark:to-slate-700/85 dark:shadow-slate-950/20" style={{ height: `${scannedH}%`, minHeight: '5px' }} title={`${d.scanned} scanned`}>
                <div className="absolute bottom-0 left-0 right-0 rounded-t-md bg-gradient-to-t from-rose-600 to-rose-400 shadow-sm shadow-rose-500/25 dark:from-rose-500 dark:to-rose-300" style={{ height: scannedH ? `${(scamH / scannedH) * 100}%` : '0%' }} title={`${d.scams} scams`} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-2 flex justify-between text-[10px] font-medium text-slate-400 tabular-nums">
        {data.map((d) => <span key={d.date} className="flex-1 text-center">{d.day}</span>)}
      </div>
    </GlassCard>
  );
}

export function ReportsPage() {
  const [period, setPeriod] = useState('');
  const { reports, loading, error } = useReports(period);
  const { stats } = useStats();
  const { data: dailyData, loading: dailyLoading } = useDailyStats();
  const { data: senderStats } = useSenderStats();

  const scamsLastWeek = stats?.scams_last_7_days ?? 0;
  const trendPct = senderStats?.scam_trend_pct ?? 0;
  const trendLabel = trendPct > 0 ? `+${trendPct}%` : trendPct < 0 ? `${trendPct}%` : 'Stable';

  const mostImpersonated = senderStats?.most_impersonated ?? '—';
  const highestRisk = senderStats?.highest_risk_sender ?? '—';

  return (
    <PageShell>
      <NavBar />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-7 pb-24 md:pb-8 space-y-5">

        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-violet-600 mb-1">Insights</div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Reports</h1>
          <p className="text-sm text-slate-500 mt-1">A bird's-eye view of detections across your inbox.</p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <KpiTile
            icon={ShieldAlert}
            tone="rose"
            label="Scams Blocked"
            value={scamsLastWeek}
            sub="last 7 days"
          />
          <KpiTile
            icon={TrendingUp}
            tone="emerald"
            label="Scam Trend"
            value={trendLabel}
            sub="vs last week"
          />
          <KpiTile
            icon={Users}
            tone="violet"
            label="Most Impersonated"
            value={mostImpersonated}
            sub="top scam domain"
          />
          <KpiTile
            icon={AlertTriangle}
            tone="amber"
            label="Highest Risk Sender"
            value={highestRisk}
            sub="most scam activity"
          />
        </div>

        <ReportsOverview data={dailyData} loading={dailyLoading} />

        <div className="flex items-center justify-between gap-4 flex-wrap pt-2">
          <h2 className="text-sm font-semibold text-slate-700">Reports</h2>
          <FilterBar
            value={period}
            onChange={(v) => setPeriod(v)}
            options={PERIOD_OPTIONS}
          />
        </div>

        {loading && <div className="py-16 text-center text-sm text-slate-400">Loading…</div>}
        {error && <div className="py-4 text-center text-sm text-rose-600">Failed to load reports.</div>}
        {!loading && !error && reports.length === 0 && (
          <GlassCard className="p-12 text-center">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center text-indigo-500 mb-3">
              <FileSearch size={26} strokeWidth={1.8} />
            </div>
            <div className="text-base font-semibold text-slate-800">No reports yet</div>
            <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
              Run a scan to generate your first report. Aggregates appear here as scans accumulate.
            </p>
          </GlassCard>
        )}
        {!loading && !error && reports.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2">
            {reports.map((report, i) => (
              <ReportCard
                key={`${report.period}-${report.generated_at}-${i}`}
                report={report}
                featured={i === 0 && period === ''}
              />
            ))}
          </div>
        )}

      </main>
      <MobileTabBar />
    </PageShell>
  );
}
