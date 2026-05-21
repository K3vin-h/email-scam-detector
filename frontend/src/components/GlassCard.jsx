export function GlassCard({ children, className = '', noBg = false, hover = false }) {
  return (
    <div className={`backdrop-blur-md border border-white/60 shadow-lg shadow-slate-200/40 rounded-xl dark:border-slate-700/70 dark:shadow-slate-950/30 ${
      noBg ? '' : 'bg-white/70'
    } ${
      hover ? 'transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-slate-300/35 dark:hover:shadow-lg dark:hover:shadow-black/35 dark:hover:border-slate-600/80' : ''
    } ${className}`}>
      {children}
    </div>
  );
}
