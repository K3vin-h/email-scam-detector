export function TextInput({ id, label, helper, type = 'text', value, onChange, min, max, error, placeholder }) {
  return (
    <div>
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700 mb-1.5">
          {label}
        </label>
      )}
      <input
        id={id}
        type={type}
        value={value ?? ''}
        onChange={onChange}
        min={min}
        max={max}
        placeholder={placeholder}
        className={`block w-full rounded-xl border px-4 py-2.5 text-sm text-slate-900 bg-white/80 backdrop-blur-sm transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-300 ${
          error ? 'border-rose-300' : 'border-slate-200'
        }`}
      />
      {helper && !error && <p className="mt-1 text-xs text-slate-400">{helper}</p>}
      {error && <p className="mt-1 text-xs text-rose-500">{error}</p>}
    </div>
  );
}
