import { useEmails } from '../hooks/useEmails.js';
import { useStats } from '../hooks/useStats.js';
import { clearDemoMode, isDemoMode } from '../hooks/useAuth.js';
import { api } from '../api/client.js';
import { NavBar } from '../components/NavBar.jsx';
import { MobileTabBar } from '../components/MobileTabBar.jsx';
import { PageShell } from '../components/PageShell.jsx';
import { GlassCard } from '../components/GlassCard.jsx';
import { EmailRow } from '../components/EmailRow.jsx';
import { FilterBar } from '../components/FilterBar.jsx';
import { Pagination } from '../components/Pagination.jsx';
import { SecurityHero } from '../components/SecurityHero.jsx';
import { StatCard } from '../components/StatCard.jsx';
import { FlaskConical, X } from 'lucide-react';

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

export function DashboardPage() {
  const { stats, loading: statsLoading, refreshing: statsRefreshing, refetch: refetchStats } = useStats();
  const {
    emails,
    count,
    page,
    setPage,
    filter,
    changeFilter,
    loading: emailsLoading,
    refreshing: emailsRefreshing,
    error: emailsError,
    refetch: refetchEmails,
    updateEmail,
  } = useEmails();

  const handleScanComplete = () => {
    refetchStats();
    refetchEmails();
  };
  const handleCorrectRisk = async (email, riskLevel) => {
    const riskLabel = riskLevel === 'possible_scam'
      ? 'Possible scam'
      : riskLevel === 'scam'
        ? 'Scam'
        : 'Legit';
    updateEmail(email.gmail_id, {
      risk_level: riskLevel,
      risk_label: riskLabel,
      user_risk_override: riskLevel,
    });
    if (!isDemoMode()) {
      await api.correctEmailRisk(email.id, riskLevel);
      refetchStats();
      refetchEmails();
    }
  };
  const threatRatio = stats?.total_scanned > 0
    ? (stats.total_scams / stats.total_scanned * 100).toFixed(1)
    : '0.0';

  return (
    <PageShell>
      <NavBar />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-7 pb-24 md:pb-8 space-y-5">

        {isDemoMode() && <DemoBanner />}

        <SecurityHero
          stats={stats}
          statsLoading={statsLoading}
          onScanComplete={handleScanComplete}
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <StatCard
            label="Total Scanned"
            value={stats?.total_scanned ?? 0}
            sub="All time"
            loading={statsLoading}
          />
          <StatCard
            label="Scams Blocked"
            value={stats?.total_scams ?? 0}
            sub="All time"
            variant="danger"
            loading={statsLoading}
          />
          <StatCard
            label="Threat Ratio"
            value={threatRatio}
            suffix="%"
            sub="All time"
            variant="rate"
            loading={statsLoading}
          />
        </div>

        <GlassCard className="overflow-visible">
          <div className="px-4 py-3 border-b border-slate-200/70 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-slate-800 tracking-tight">Recent activity</h2>
                {(emailsRefreshing || statsRefreshing) && (
                  <span className="inline-flex h-1.5 w-1.5 rounded-full bg-indigo-500 animate-pulse" aria-label="Refreshing" />
                )}
              </div>
              <p className="text-sm text-slate-500 mt-0.5">Sorted by most recent scan results.</p>
            </div>
            <FilterBar value={filter} onChange={changeFilter} />
          </div>

          {emailsLoading && emails.length === 0 ? (
            <div className="py-16 text-center text-sm text-slate-400">Loading…</div>
          ) : emailsError ? (
            <div className="py-16 text-center text-sm text-rose-600">Failed to load emails. Try again.</div>
          ) : emails.length === 0 ? (
            <div className="py-16 text-center text-sm text-slate-400">No emails found. Run a scan to get started.</div>
          ) : (
            <>
              <div className="divide-y divide-slate-100/80 dark:divide-slate-800/80">
                {emails.map((email) => (
                  <EmailRow key={email.gmail_id} email={email} onCorrectRisk={handleCorrectRisk} />
                ))}
              </div>
              <Pagination page={page} count={count} onPageChange={setPage} />
            </>
          )}
        </GlassCard>

      </main>
      <MobileTabBar />
    </PageShell>
  );
}
