import { useEmails } from '../hooks/useEmails.js';
import { useStats } from '../hooks/useStats.js';
import { StatCard } from '../components/StatCard.jsx';
import { EmailRow } from '../components/EmailRow.jsx';
import { FilterBar } from '../components/FilterBar.jsx';
import { Pagination } from '../components/Pagination.jsx';
import { ScanButton } from '../components/ScanButton.jsx';

export function DashboardPage() {
  const { stats, loading: statsLoading, refetch: refetchStats } = useStats();
  const {
    emails, count, page, setPage, filter, changeFilter, loading: emailsLoading, error: emailsError,
  } = useEmails();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <ScanButton onComplete={refetchStats} />
      </div>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard label="Total Scanned"  value={stats?.total_scanned}       loading={statsLoading} />
        <StatCard label="Total Scams"    value={stats?.total_scams}          loading={statsLoading} variant="danger" />
        <StatCard label="Scams (7 days)" value={stats?.scams_last_7_days}    loading={statsLoading} variant="danger" />
        <StatCard label="Scams (30 days)" value={stats?.scams_last_30_days}  loading={statsLoading} variant="danger" />
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-sm font-semibold text-slate-700">Emails</h2>
          <FilterBar value={filter} onChange={changeFilter} />
        </div>

        {emailsLoading ? (
          <div className="py-16 text-center text-sm text-slate-400">Loading…</div>
        ) : emailsError ? (
          <div className="py-16 text-center text-sm text-rose-600">Failed to load emails. Try again.</div>
        ) : emails.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-400">
            No emails found. Run a scan to get started.
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wide">From</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Subject</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Confidence</th>
                    <th className="px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wide">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {emails.map((email) => (
                    <EmailRow key={email.gmail_id} email={email} />
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={page} count={count} onPageChange={setPage} />
          </>
        )}
      </div>
    </div>
  );
}
