import { useRef, useEffect, useState } from 'react';

const EMAIL_OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Scam only', value: 'true' },
  { label: 'Legit only', value: 'false' },
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
        className="relative inline-flex bg-slate-100/80 backdrop-blur-sm rounded-full p-1 border border-slate-200/60"
      >
        <div
          aria-hidden="true"
          className="absolute top-1 bottom-1 bg-white rounded-full shadow-sm shadow-slate-300/40 transition-all duration-300 ease-out pointer-events-none"
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
              value === opt.value ? 'text-slate-900' : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
