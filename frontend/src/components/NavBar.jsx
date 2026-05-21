import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { ShieldCheck, LogOut, User } from 'lucide-react';
import { api } from '../api/client.js';
import { ThemeToggle } from './ThemeToggle.jsx';
import { useUnsavedChanges } from './UnsavedChangesContext.jsx';

function getCsrfToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

function handleSignOut() {
  fetch('/admin/logout/', {
    method: 'POST',
    credentials: 'include',
    headers: { 'X-CSRFToken': getCsrfToken() },
  }).finally(() => {
    window.location.href = '/login';
  });
}

function NavItem({ to, end, children }) {
  const unsaved = useUnsavedChanges();
  const guard = unsaved?.guard;

  return (
    <NavLink
      to={to}
      end={end}
      onClick={(event) => {
        if (!guard?.active) return;
        event.preventDefault();
        guard.onBlocked?.();
      }}
      className={({ isActive }) =>
        `relative px-3.5 py-2 text-sm font-semibold transition-colors pb-3 ${
          isActive ? 'text-indigo-600' : 'text-slate-500 hover:text-slate-900'
        }`
      }
    >
      {({ isActive }) => (
        <>
          {children}
          {isActive && (
            <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-indigo-500 rounded-full" />
          )}
        </>
      )}
    </NavLink>
  );
}

export function NavBar() {
  const [online, setOnline] = useState(null);

  useEffect(() => {
    api.getHealth().then(() => setOnline(true)).catch(() => setOnline(false));
  }, []);

  return (
    <header className="hidden md:block bg-white/80 backdrop-blur-md border-b border-slate-200/60 sticky top-0 z-20 dark:bg-slate-950/75 dark:border-slate-800/80">
      <nav className="max-w-5xl mx-auto px-6 h-16 flex items-center">

        {/* Left: wordmark */}
        <div className="flex items-center gap-2.5 text-slate-900 font-bold text-lg tracking-tight shrink-0">
          <ShieldCheck size={20} className="text-indigo-600" strokeWidth={2.5} />
          Scam Filter
        </div>

        {/* Center: nav links */}
        <div className="flex-1 flex justify-center items-center gap-0">
          <NavItem to="/" end>Dashboard</NavItem>
          <NavItem to="/reports">Reports</NavItem>
          <NavItem to="/settings">Settings</NavItem>
        </div>

        {/* Right: online indicator + avatar + sign-out */}
        <div className="flex items-center gap-3 shrink-0">
          <ThemeToggle />

          {/* Local AI status */}
          <div className="flex items-center gap-1.5">
            <span className="relative flex h-2 w-2">
              {online === true && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${
                online === null ? 'bg-slate-300' :
                online ? 'bg-emerald-400' : 'bg-red-400'
              }`} />
            </span>
            <span className="text-[11px] font-medium text-slate-400">Local AI</span>
          </div>

          {/* Generic avatar */}
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 flex items-center justify-center text-white">
            <User size={13} strokeWidth={2.5} />
          </div>

          {/* Sign out */}
          <button
            onClick={handleSignOut}
            className="flex items-center text-slate-400 hover:text-slate-700 transition-colors"
            aria-label="Sign out"
          >
            <LogOut size={15} />
          </button>
        </div>

      </nav>
    </header>
  );
}
