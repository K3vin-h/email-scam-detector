import { Inbox, ShieldAlert, ShieldCheck, TrendingUp } from 'lucide-react';
import { GlassCard } from './GlassCard.jsx';

const VARIANTS = {
  default: { Icon: Inbox,       iconBg: 'bg-indigo-50',  iconText: 'text-indigo-600',  ring: 'ring-indigo-100',  valText: 'text-slate-900', tint: 'from-indigo-500/10 to-indigo-500/0' },
  danger:  { Icon: ShieldAlert, iconBg: 'bg-rose-50',    iconText: 'text-rose-600',    ring: 'ring-rose-100',    valText: 'text-rose-600',  tint: 'from-rose-500/12 to-rose-500/0' },
  success: { Icon: ShieldCheck, iconBg: 'bg-emerald-50', iconText: 'text-emerald-600', ring: 'ring-emerald-100', valText: 'text-emerald-600', tint: 'from-emerald-500/12 to-emerald-500/0' },
  rate:    { Icon: TrendingUp,  iconBg: 'bg-violet-50',  iconText: 'text-violet-600',  ring: 'ring-violet-100',  valText: 'text-violet-600', tint: 'from-violet-500/12 to-violet-500/0' },
};

export function StatCard({ label, value, suffix, sub, variant = 'default', loading = false }) {
  const v = VARIANTS[variant] ?? VARIANTS.default;

  return (
    <GlassCard hover className="p-5 relative overflow-hidden">
      <div className={`absolute inset-0 bg-gradient-to-br ${v.tint} pointer-events-none`} />
      <div className="relative flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider leading-tight">{label}</p>
          {loading ? (
            <div className="mt-3 h-10 w-24 bg-slate-100 rounded-lg animate-pulse" />
          ) : (
            <p className={`mt-2 text-4xl font-bold tracking-tight tabular-nums ${v.valText}`}>
              {value ?? '—'}{suffix && <span className="ml-0.5 text-2xl font-semibold">{suffix}</span>}
            </p>
          )}
          {sub && <p className="mt-1 text-xs font-medium text-slate-500">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl ring-4 flex items-center justify-center shrink-0 ${v.ring} ${v.iconBg} ${v.iconText}`}>
          <v.Icon size={18} strokeWidth={2} />
        </div>
      </div>
    </GlassCard>
  );
}
