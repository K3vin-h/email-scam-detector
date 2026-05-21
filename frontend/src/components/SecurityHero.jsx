import { Clock, ShieldCheck, ShieldAlert } from 'lucide-react';
import { ScanButton } from './ScanButton.jsx';
import { GlassCard } from './GlassCard.jsx';

export function SecurityHero({ stats, statsLoading, onScanComplete }) {
  const hasThreats = !statsLoading && stats?.total_scams > 0;
  const allClear = !statsLoading && !hasThreats;

  const title = statsLoading
    ? null
    : hasThreats
      ? `${stats.total_scams} threat${stats.total_scams !== 1 ? 's' : ''} detected`
      : 'Your inbox is protected';
  const subtitle = statsLoading
    ? null
    : hasThreats
      ? `${stats.total_scanned ?? 0} emails scanned with suspicious messages ready for review.`
      : `${stats?.total_scanned ?? 0} emails scanned with no scam detections.`;
  const tone = hasThreats
      ? {
        tint: 'bg-rose-50/70 dark:bg-rose-950/20',
        chip: 'bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-500/10 dark:text-rose-300 dark:border-rose-500/30',
        ring: 'from-rose-500 to-orange-500',
        title: 'text-rose-700 dark:text-rose-300',
      }
    : {
        tint: 'bg-emerald-50/70 dark:bg-emerald-950/18',
        chip: 'bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:border-emerald-500/25',
        ring: 'from-emerald-500 to-teal-500',
        title: 'text-emerald-700 dark:text-emerald-200',
      };

  return (
    <GlassCard className="relative overflow-hidden p-5 sm:p-6">
      <div className={`absolute inset-0 ${tone.tint} opacity-80 pointer-events-none`} />
      <div className="relative flex flex-col sm:flex-row sm:items-center gap-5">
        <div className="flex items-center gap-5 flex-1 min-w-0">
          <div className="relative shrink-0">
            <div className={`absolute inset-0 rounded-2xl blur-xl opacity-45 bg-gradient-to-br ${tone.ring}`} />
            <div className={`relative w-16 h-16 rounded-2xl flex items-center justify-center text-white shadow-lg bg-gradient-to-br ${tone.ring}`}>
              {allClear ? <ShieldCheck size={26} strokeWidth={2} /> : <ShieldAlert size={26} strokeWidth={2} />}
            </div>
          </div>

          <div className="min-w-0">
            {statsLoading ? (
              <div className="space-y-2">
                <div className="h-7 w-36 bg-slate-100 rounded-lg animate-pulse" />
                <div className="h-4 w-52 bg-slate-100 rounded-lg animate-pulse" />
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border uppercase tracking-wider ${tone.chip}`}>
                    <span className="w-1 h-1 rounded-full bg-current" />
                    {hasThreats ? 'Threats blocked' : 'All clear'}
                  </span>
                  <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
                    <Clock size={11} strokeWidth={2.2} /> Next scan in 6h
                  </span>
                </div>
                <h1 className={`text-2xl font-bold tracking-tight ${tone.title}`}>
                  {title}
              </h1>
                <p className="mt-1 text-sm text-slate-600">{subtitle}</p>
              </>
            )}
          </div>
        </div>

        <ScanButton onComplete={onScanComplete} />
      </div>
    </GlassCard>
  );
}
