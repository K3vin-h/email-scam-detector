import { useEmails } from '../hooks/useEmails.js';
import { useStats } from '../hooks/useStats.js';
import { NavBar } from '../components/NavBar.jsx';
import { MobileTabBar } from '../components/MobileTabBar.jsx';
import { PageShell } from '../components/PageShell.jsx';
import { GlassCard } from '../components/GlassCard.jsx';
import { EmailRow } from '../components/EmailRow.jsx';
import { FilterBar } from '../components/FilterBar.jsx';
import { Pagination } from '../components/Pagination.jsx';
import { SecurityHero } from '../components/SecurityHero.jsx';
import { StatCard } from '../components/StatCard.jsx';

export function DashboardPage() {
  const { stats, loading: statsLoading, refetch: refetchStats } = useStats();
  const {
    emails,
    count,
    page,
    setPage,
    filter,
    changeFilter,
    loading: emailsLoading,
    error: emailsError,
    refetch: refetchEmails,
  } = useEmails();

  const handleScanComplete = () => {
    refetchStats();
    refetchEmails();
  };
  const threatRatio = stats?.total_scanned > 0
    ? (stats.total_scams / stats.total_scanned * 100).toFixed(1)
    : '0.0';

  return (
    <PageShell>
      <NavBar />
      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-7 pb-24 md:pb-8 space-y-5">

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

        <GlassCard className="overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-200/70 flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h2 className="text-base font-semibold text-slate-800 tracking-tight">Recent activity</h2>
              <p className="text-sm text-slate-500 mt-0.5">Sorted by most recent scan results.</p>
            </div>
            <FilterBar value={filter} onChange={changeFilter} />
          </div>

          {emailsLoading ? (
            <div className="py-16 text-center text-sm text-slate-400">Loading…</div>
          ) : emailsError ? (
            <div className="py-16 text-center text-sm text-rose-600">Failed to load emails. Try again.</div>
          ) : emails.length === 0 ? (
            <div className="py-16 text-center text-sm text-slate-400">No emails found. Run a scan to get started.</div>
          ) : (
            <>
              <div className="divide-y divide-slate-100/80">
                {emails.map((email) => (
                  <EmailRow key={email.gmail_id} email={email} />
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
