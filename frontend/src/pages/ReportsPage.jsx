import { useState } from 'react';
import { ShieldAlert, TrendingUp, TrendingDown, Users, AlertTriangle, FlaskConical, X } from 'lucide-react';
import { useReports } from '../hooks/useReports.js';
import { useStats } from '../hooks/useStats.js';
import { useDailyStats } from '../hooks/useDailyStats.js';
import { useSenderStats } from '../hooks/useSenderStats.js';
import { clearDemoMode, isDemoMode } from '../hooks/useAuth.js';
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

function DemoBanner() {
  function exitDemo() {
    clearDemoMode();
    window.location.href = '/login';
  }
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-amber-50/80 border border-amber-200/60 text-amber-800 dark:bg-amber-950/30 dark:border-amber-700/30 dark:text-amber-300">
      <div className="flex items-center gap-2 text-sm font-medium">
        <FlaskConical size={15} strokeWidth={2} />
        Demo mode — placeholder data only, no real Gmail connection
      </div>
      <button
        onClick={exitDemo}
        className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-100/80 hover:bg-amber-200/80 transition-colors dark:bg-amber-900/40 dark:hover:bg-amber-800/50"
      >
        <X size={11} strokeWidth={2.5} />
        Exit demo
      </button>
    </div>
  );
}

function DetectionChart({ data, loading }) {
  if (loading || !data.length) return null;
  const maxScanned = Math.max(...data.map((d) => d.scanned), 1);
  const totalScanned = data.reduce((sum, d) => sum + d.scanned, 0);
  const totalScams = data.reduce((sum, d) => sum + d.scams, 0);

  return (
    <GlassCard className="p-5 sm:p-6">
      <div className="flex items-start justify-between flex-wrap gap-4 mb-6">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-violet-600 dark:text-violet-400 mb-1">
            Last 7 days
          </div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            Detections over time
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Daily scan volume and confirmed scams.
          </p>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-right">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-0.5">
              Scanned
            </div>
            <div className="text-2xl font-bold tabular-nums text-slate-900 dark:text-slate-100">
              {totalScanned.toLocaleString()}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-0.5">
              Scams
            </div>
            <div className="text-2xl font-bold tabular-nums text-rose-600 dark:text-rose-400">
              {totalScams.toLocaleString()}
            </div>
          </div>
        </div>
      </div>

      <div className="relative flex items-end gap-2 sm:gap-3 h-56 rounded-xl border border-slate-200/70 dark:border-slate-700/60 bg-slate-50/60 dark:bg-slate-900/50 px-4 pt-5 pb-3">
        {/* grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none px-4">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="border-t border-slate-200/50 dark:border-slate-700/50" />
          ))}
        </div>
        {data.map((d) => {
          const scannedH = Math.max(Math.round((d.scanned / maxScanned) * 100), 3);
          const scamH = d.scanned > 0 ? Math.round((d.scams / d.scanned) * scannedH) : 0;
          return (
            <div
              key={d.date}
              className="group relative z-10 flex-1 h-full flex flex-col justify-end min-w-0"
            >
              {/* hover tooltip */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                <div className="bg-slate-900 dark:bg-slate-800 text-white dark:text-slate-100 text-[10px] font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-xl dark:border dark:border-slate-700">
                  <span className="text-slate-300">{d.day}:</span>{' '}
                  <span className="text-rose-300">{d.scams} scam{d.scams !== 1 ? 's' : ''}</span>
                  <span className="text-slate-400"> / {d.scanned} scanned</span>
                </div>
              </div>
              {/* bar */}
              <div
                className="relative w-full rounded-t-md overflow-hidden bg-slate-300 dark:bg-slate-600 group-hover:bg-slate-400/80 dark:group-hover:bg-slate-500 transition-colors"
                style={{ height: `${scannedH}%`, minHeight: '4px' }}
              >
                <div
                  className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-rose-500 via-rose-400 to-pink-400 rounded-t-sm"
                  style={{ height: scannedH ? `${(scamH / scannedH) * 100}%` : '0%' }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex justify-between">
        {data.map((d) => (
          <span
            key={d.date}
            className="flex-1 text-center text-[11px] font-medium text-slate-400 dark:text-slate-500"
          >
            {d.day}
          </span>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-slate-300 dark:bg-slate-600" />
          Scanned
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-sm bg-rose-400" />
          Scams
        </span>
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
  const trendTone = trendPct > 0 ? 'rose' : 'emerald';
  const TrendIcon = trendPct > 0 ? TrendingUp : TrendingDown;

  const mostImpersonated = senderStats?.most_impersonated ?? '—';
  const highestRisk = senderStats?.highest_risk_sender ?? '—';

  return (
    <PageShell>
      <NavBar />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-7 pb-24 md:pb-8 space-y-5">

        {isDemoMode() && <DemoBanner />}

        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wider text-violet-600 dark:text-violet-400 mb-1">
            Insights
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">Reports</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            A bird's-eye view of detections across your inbox.
          </p>
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
            icon={TrendIcon}
            tone={trendTone}
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

        <DetectionChart data={dailyData} loading={dailyLoading} />

        <GlassCard className="overflow-visible">
          <div className="px-4 py-3 border-b border-slate-200/70 dark:border-slate-700/60 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-base font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
                Generated reports
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
                Summary snapshots of scan activity.
              </p>
            </div>
            <FilterBar
              value={period}
              onChange={(v) => setPeriod(v)}
              options={PERIOD_OPTIONS}
            />
          </div>

          {loading && (
            <div className="py-16 text-center text-sm text-slate-400 dark:text-slate-500">
              Loading…
            </div>
          )}
          {error && (
            <div className="py-16 text-center text-sm text-rose-600 dark:text-rose-400">
              Failed to load reports.
            </div>
          )}
          {!loading && !error && reports.length === 0 && (
            <div className="py-16 flex flex-col items-center gap-3 text-center px-6">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-50 to-violet-100 dark:from-indigo-900/30 dark:to-violet-900/30 flex items-center justify-center text-indigo-400 dark:text-indigo-300">
                <ShieldAlert size={22} strokeWidth={1.8} />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">No reports yet</p>
                <p className="text-xs text-slate-400 dark:text-slate-500 mt-1 max-w-xs mx-auto">
                  Run a scan to generate your first report. Aggregates appear here as scans accumulate.
                </p>
              </div>
            </div>
          )}
          {!loading && !error && reports.length > 0 && (
            <div className="p-4 grid gap-4 md:grid-cols-2">
              {reports.map((report, i) => (
                <ReportCard
                  key={`${report.period}-${report.generated_at}-${i}`}
                  report={report}
                  featured={i === 0 && period === ''}
                />
              ))}
            </div>
          )}
        </GlassCard>

      </main>
      <MobileTabBar />
    </PageShell>
  );
}
