export function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Scam Filter</h1>
          <p className="mt-2 text-slate-500 text-sm">Gmail scam detection, locally hosted.</p>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900 mb-2">Sign in to continue</h2>
          <p className="text-sm text-slate-500 mb-6">
            Use your local Django admin account to access the dashboard.
          </p>
          <a
            href="/admin/login/?next=/"
            className="inline-flex items-center justify-center w-full px-4 py-2.5 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-700 transition-colors"
          >
            Sign In
          </a>
          <p className="mt-4 text-xs text-slate-400">
            After signing in you'll be returned here automatically.
          </p>
        </div>
      </div>
    </div>
  );
}
