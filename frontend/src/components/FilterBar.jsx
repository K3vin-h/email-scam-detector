import { useRef, useEffect, useState } from 'react';

const EMAIL_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Legit', value: 'legit' },
  { label: 'Possible scam', value: 'possible_scam' },
  { label: 'Scam', value: 'scam' },
];

export function FilterBar({ value, onChange, options = EMAIL_OPTIONS }) {
  const containerRef = useRef(null);
  const buttonRefs = useRef({});
  const [pill, setPill] = useState({ left: 0, width: 0 });

  useEffect(() => {
    const el = buttonRefs.current[value];
    if (el) setPill({ left: el.offsetLeft, width: el.offsetWidth });
  }, [value, options]);

  return (
    <div className="overflow-x-auto max-w-full [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      <div
        ref={containerRef}
        role="group"
        aria-label="Email filter"
        className="relative inline-flex bg-slate-100/80 backdrop-blur-sm rounded-full p-1 border border-slate-200/60 dark:bg-slate-900/70 dark:border-slate-700/80"
      >
        <div
          aria-hidden="true"
          className="absolute top-1 bottom-1 bg-white rounded-full shadow-sm shadow-slate-300/40 transition-all duration-300 ease-out pointer-events-none dark:bg-slate-700 dark:shadow-slate-950/40"
          style={{ left: pill.left, width: pill.width }}
        />
        {options.map((opt) => (
          <button
            key={opt.value}
            ref={(el) => { buttonRefs.current[opt.value] = el; }}
            type="button"
            onClick={() => onChange(opt.value)}
            aria-pressed={value === opt.value}
            className={`relative z-10 px-4 py-1.5 text-sm font-medium rounded-full transition-colors whitespace-nowrap ${
              value === opt.value ? 'text-slate-900 dark:text-slate-50' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
