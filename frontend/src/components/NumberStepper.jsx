export function NumberStepper({ id, label, helper, value, onChange, min, max, step = 1 }) {
  const decrement = () => onChange(Math.max(min ?? -Infinity, value - step));
  const increment = () => onChange(Math.min(max ?? Infinity, value + step));

  return (
    <div>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1.5">
          {label}
        </label>
      )}
      <div className="flex items-center rounded-xl border border-slate-200 bg-white/80 backdrop-blur-sm overflow-hidden">
        <button
          type="button"
          onClick={decrement}
          disabled={min !== undefined && value <= min}
          className="px-4 py-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors border-r border-slate-200 disabled:opacity-30 disabled:cursor-not-allowed text-xl leading-none select-none"
          aria-label="Decrease"
        >
          −
        </button>
        <span
          id={id}
          className="flex-1 text-center text-sm font-semibold tabular-nums text-slate-900 py-2.5 select-none"
        >
          {value}
        </span>
        <button
          type="button"
          onClick={increment}
          disabled={max !== undefined && value >= max}
          className="px-4 py-2.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors border-l border-slate-200 disabled:opacity-30 disabled:cursor-not-allowed text-xl leading-none select-none"
          aria-label="Increase"
        >
          +
        </button>
      </div>
      {helper && <p className="mt-1 text-xs text-slate-400">{helper}</p>}
    </div>
  );
}
