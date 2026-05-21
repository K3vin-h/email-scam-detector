import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './hooks/useAuth.js';
import { LoginPage } from './pages/LoginPage.jsx';
import { DashboardPage } from './pages/DashboardPage.jsx';
import { ReportsPage } from './pages/ReportsPage.jsx';
import { SettingsPage } from './pages/SettingsPage.jsx';
import { UnsavedChangesProvider } from './components/UnsavedChangesContext.jsx';

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="flex items-center gap-2 text-slate-400">
        <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span className="text-sm">Loading…</span>
      </div>
    </div>
  );
}

function ProtectedLayout() {
  const { authenticated, loading, error } = useAuth();
  if (loading) return <LoadingScreen />;
  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-6">
        <div className="max-w-md rounded-xl border border-rose-200 bg-rose-50 px-6 py-5 text-center">
          <h1 className="text-base font-semibold text-rose-800">Unable to verify session</h1>
          <p className="mt-2 text-sm text-rose-700">
            The backend could not be reached. Please check the server and try again.
          </p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-white border border-rose-200 text-sm font-medium text-rose-700 rounded-lg hover:bg-rose-100 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  if (!authenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <UnsavedChangesProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<ProtectedLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </UnsavedChangesProvider>
  );
}
