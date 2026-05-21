import { TrendingUp, TrendingDown } from 'lucide-react';
import { GlassCard } from './GlassCard.jsx';

const TONES = {
  indigo:  { ring: 'ring-indigo-100',  bg: 'bg-indigo-50',  text: 'text-indigo-600',  tint: 'from-indigo-500/10 to-indigo-500/0' },
  rose:    { ring: 'ring-rose-100',    bg: 'bg-rose-50',    text: 'text-rose-600',    tint: 'from-rose-500/12 to-rose-500/0' },
  emerald: { ring: 'ring-emerald-100', bg: 'bg-emerald-50', text: 'text-emerald-600', tint: 'from-emerald-500/12 to-emerald-500/0' },
  violet:  { ring: 'ring-violet-100',  bg: 'bg-violet-50',  text: 'text-violet-600',  tint: 'from-violet-500/12 to-violet-500/0' },
  amber:   { ring: 'ring-amber-100',   bg: 'bg-amber-50',   text: 'text-amber-600',   tint: 'from-amber-500/14 to-amber-500/0' },
};

export function KpiTile({ icon: Icon, label, value, sub, tone = 'indigo', delta }) {
  const t = TONES[tone] ?? TONES.indigo;
  const deltaPositive = delta?.startsWith('+');

  return (
    <GlassCard hover className="p-4 relative overflow-hidden">
      <div className={`absolute inset-0 bg-gradient-to-br ${t.tint} pointer-events-none`} />
      <div className="relative flex items-start justify-between mb-3">
        <div className={`w-8 h-8 rounded-xl ring-1 flex items-center justify-center ${t.ring} ${t.bg} ${t.text}`}>
          <Icon size={16} strokeWidth={2} />
        </div>
        {delta && (
          <span className={`inline-flex items-center gap-0.5 text-[10px] font-semibold rounded-full px-1.5 py-0.5 ${
            deltaPositive ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'
          }`}>
            {deltaPositive ? <TrendingUp size={10} strokeWidth={2.5} /> : <TrendingDown size={10} strokeWidth={2.5} />}
            {delta}
          </span>
        )}
      </div>
      <div className="relative text-xs font-medium text-slate-500">{label}</div>
      <div className="relative mt-0.5 text-2xl font-bold text-slate-900 tracking-tight tabular-nums truncate">{value}</div>
      {sub && <div className="relative text-[11px] text-slate-400 mt-1 truncate">{sub}</div>}
    </GlassCard>
  );
}
