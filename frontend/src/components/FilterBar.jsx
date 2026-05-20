const OPTIONS = [
  { label: 'All', value: '' },
  { label: 'Scam only', value: 'true' },
  { label: 'Legit only', value: 'false' },
];

export function FilterBar({ value, onChange }) {
  return (
    <div role="group" aria-label="Email filter" className="flex gap-1 p-1 bg-slate-100 rounded-lg w-fit">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          aria-pressed={value === opt.value}
          className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
            value === opt.value
              ? 'bg-white text-slate-900 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
