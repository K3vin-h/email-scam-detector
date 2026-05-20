export function StatCard({ label, value, variant = 'default', loading = false }) {
  const valueColors = {
    default: 'text-slate-900',
    danger: 'text-rose-600',
    success: 'text-emerald-600',
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{label}</p>
      {loading ? (
        <div className="mt-2 h-9 w-20 bg-slate-100 rounded animate-pulse" />
      ) : (
        <p className={`mt-1 text-4xl font-bold tabular-nums ${valueColors[variant]}`}>
          {value ?? '—'}
        </p>
      )}
    </div>
  );
}
