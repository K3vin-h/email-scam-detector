export function Toggle({ id, label, checked, onChange, showLabel = true }) {
  return (
    <div className="flex items-center gap-3">
      <button
        id={id}
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 active:scale-95 focus-visible:ring-2 focus-visible:ring-indigo-400 focus-visible:outline-none ${
          checked ? 'bg-gradient-to-r from-indigo-500 to-violet-500' : 'bg-slate-200'
        }`}
      >
        <span className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? 'translate-x-[1.4rem]' : 'translate-x-0.5'
        }`} />
      </button>
      {label && showLabel && (
        <label htmlFor={id} className="text-sm font-medium text-slate-700 cursor-pointer select-none">
          {label}
        </label>
      )}
    </div>
  );
}
