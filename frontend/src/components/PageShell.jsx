export function PageShell({ children }) {
  return (
    <div className="relative min-h-screen bg-slate-50 overflow-x-hidden transition-colors dark:bg-slate-950">
      <div className="relative z-10">
        {children}
      </div>
    </div>
  );
}
