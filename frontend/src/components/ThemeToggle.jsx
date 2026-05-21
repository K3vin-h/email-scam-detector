import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

function preferredTheme() {
  const saved = localStorage.getItem('scam-filter-theme');
  if (saved === 'dark' || saved === 'light') return saved;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
}

export function ThemeToggle() {
  const [theme, setTheme] = useState(() => preferredTheme());
  const isDark = theme === 'dark';

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (!window.matchMedia) return undefined;
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const syncSystemTheme = () => {
      if (localStorage.getItem('scam-filter-theme')) return;
      setTheme(media.matches ? 'dark' : 'light');
    };
    media.addEventListener('change', syncSystemTheme);
    return () => media.removeEventListener('change', syncSystemTheme);
  }, []);

  return (
    <button
      type="button"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      onClick={() => {
        const nextTheme = isDark ? 'light' : 'dark';
        localStorage.setItem('scam-filter-theme', nextTheme);
        setTheme(nextTheme);
      }}
      className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-200/70 bg-white/70 text-slate-500 backdrop-blur-sm transition hover:border-indigo-300 hover:text-indigo-600 active:scale-95 dark:border-slate-700 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:text-indigo-300"
    >
      {isDark ? <Sun size={15} strokeWidth={2.2} /> : <Moon size={15} strokeWidth={2.2} />}
    </button>
  );
}
