import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, Settings } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle.jsx';
import { useUnsavedChanges } from './UnsavedChangesContext.jsx';

const TABS = [
  { to: '/', end: true, Icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/reports', Icon: FileText, label: 'Reports' },
  { to: '/settings', Icon: Settings, label: 'Settings' },
];

export function MobileTabBar() {
  const unsaved = useUnsavedChanges();
  const guard = unsaved?.guard;

  return (
    <>
      <div className="md:hidden fixed right-4 top-4 z-30">
        <ThemeToggle />
      </div>
      <nav aria-label="Mobile navigation" className="md:hidden fixed bottom-0 inset-x-0 z-20 bg-white/80 backdrop-blur-md border-t border-slate-200/60 dark:bg-slate-950/80 dark:border-slate-800/80">
        <div className="flex">
          {TABS.map(({ to, end, Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={(event) => {
                if (!guard?.active) return;
                event.preventDefault();
                guard.onBlocked?.();
              }}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center gap-1 py-2.5 text-[10px] font-semibold uppercase tracking-wider transition-colors ${
                  isActive ? 'text-indigo-600 dark:text-indigo-300' : 'text-slate-400 hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} strokeWidth={isActive ? 2 : 1.75} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  );
}
