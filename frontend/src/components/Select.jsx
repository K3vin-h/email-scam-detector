import { useEffect, useRef, useState } from 'react';
import { Check, ChevronDown } from 'lucide-react';

export function Select({ id, label, helper, value, onChange, options }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const current = options.find((opt) => opt.value === value) ?? options[0];

  useEffect(() => {
    if (!open) return undefined;
    const handlePointerDown = (event) => {
      if (ref.current && !ref.current.contains(event.target)) setOpen(false);
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', handlePointerDown);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open]);

  const selectOption = (nextValue) => {
    onChange({ target: { value: nextValue } });
    setOpen(false);
  };

  return (
    <div ref={ref}>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1.5">
          {label}
        </label>
      )}
      <div className="relative">
        <button
          id={id}
          type="button"
          aria-haspopup="listbox"
          aria-expanded={open}
          onClick={() => setOpen((next) => !next)}
          className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white/80 px-4 py-2.5 text-left text-sm text-slate-900 backdrop-blur-sm transition hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-300 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-100 dark:hover:border-slate-600 dark:focus:border-indigo-400"
        >
          <span>{current?.label}</span>
          <ChevronDown size={16} strokeWidth={2.2} className={`text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
        </button>

        {open && (
          <div
            role="listbox"
            aria-labelledby={id}
            className="absolute left-0 right-0 z-40 mt-2 overflow-hidden rounded-xl border border-slate-200 bg-slate-50/95 p-1 shadow-xl shadow-slate-300/40 backdrop-blur-md dark:border-slate-700 dark:bg-slate-900/95 dark:shadow-slate-950/45"
          >
            {options.map((opt) => {
              const selected = opt.value === value;
              return (
                <button
                  key={opt.value}
                  type="button"
                  role="option"
                  aria-selected={selected}
                  onClick={() => selectOption(opt.value)}
                  className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    selected
                      ? 'bg-slate-200/80 font-semibold text-indigo-700 dark:bg-slate-700/80 dark:text-indigo-200'
                      : 'text-slate-700 hover:bg-slate-200/70 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-50'
                  }`}
                >
                  <span>{opt.label}</span>
                  {selected && <Check size={14} strokeWidth={2.6} className="text-indigo-600 dark:text-indigo-300" />}
                </button>
              );
            })}
          </div>
        )}
      </div>
      {helper && <p className="mt-1 text-xs text-slate-400">{helper}</p>}
    </div>
  );
}
