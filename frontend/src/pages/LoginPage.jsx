import { Lock, ShieldCheck, FlaskConical } from 'lucide-react';
import { PageShell } from '../components/PageShell.jsx';
import { GlassCard } from '../components/GlassCard.jsx';
import { clearDemoMode, enterDemoMode } from '../hooks/useAuth.js';

function enterDemo() {
  enterDemoMode();
  window.location.href = '/';
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.99.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

export function LoginPage() {
  return (
    <PageShell>
      <div className="min-h-screen flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm relative">
          <div aria-hidden="true" className="absolute -inset-8 bg-gradient-to-br from-indigo-300/30 via-violet-300/20 to-fuchsia-200/20 blur-3xl rounded-full pointer-events-none" />

          <GlassCard className="relative p-8 text-center">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-400 to-violet-500 rounded-2xl blur-xl opacity-50" />
                <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/40 flex items-center justify-center text-white">
                  <ShieldCheck size={26} strokeWidth={2} />
                </div>
              </div>
            </div>

            <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Scam Filter</h1>
            <p className="mt-2 text-sm text-slate-500">Gmail scam detection, locally hosted</p>

            <a
              href="/admin/login/?next=/"
              onClick={clearDemoMode}
              className="mt-8 inline-flex items-center justify-center gap-3 w-full px-5 py-3 rounded-full font-semibold text-sm text-slate-800 bg-white/90 border border-slate-200 shadow-sm shadow-slate-900/5 backdrop-blur-sm transition-all hover:border-indigo-200 hover:bg-white hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 active:scale-95 dark:border-white/10 dark:bg-slate-900/80 dark:text-slate-100 dark:shadow-indigo-950/30 dark:hover:border-indigo-400/40 dark:hover:bg-slate-800/90 dark:focus-visible:outline-indigo-300"
            >
              <GoogleIcon />
              Sign in with Google
            </a>

            <div className="mt-3 flex items-center gap-3">
              <div className="flex-1 h-px bg-slate-200/70 dark:bg-slate-700/50" />
              <span className="text-[11px] text-slate-400 dark:text-slate-500">or</span>
              <div className="flex-1 h-px bg-slate-200/70 dark:bg-slate-700/50" />
            </div>

            <button
              onClick={enterDemo}
              className="mt-3 inline-flex items-center justify-center gap-2.5 w-full px-5 py-3 rounded-full font-semibold text-sm text-indigo-700 bg-indigo-50/80 border border-indigo-200/60 shadow-sm transition-all hover:bg-indigo-100/80 hover:border-indigo-300/60 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 active:scale-95 dark:text-indigo-300 dark:bg-indigo-950/40 dark:border-indigo-800/40 dark:hover:bg-indigo-900/40 dark:hover:border-indigo-600/40"
            >
              <FlaskConical size={16} strokeWidth={2} />
              Try demo
            </button>

            <div className="mt-5 grid grid-cols-3 gap-2 text-[10px] uppercase tracking-wider font-semibold text-slate-400">
              <div className="flex items-center gap-1.5 justify-center"><span className="w-1 h-1 rounded-full bg-emerald-500" />OAuth</div>
              <div className="flex items-center gap-1.5 justify-center"><span className="w-1 h-1 rounded-full bg-emerald-500" />Read-only</div>
              <div className="flex items-center gap-1.5 justify-center"><span className="w-1 h-1 rounded-full bg-emerald-500" />Local AI</div>
            </div>
          </GlassCard>
          <p className="mt-6 flex items-center justify-center gap-1.5 text-xs text-slate-500">
            <Lock size={11} strokeWidth={2.2} /> Protected by local AI. No data leaves your machine.
          </p>
        </div>
      </div>
    </PageShell>
  );
}
