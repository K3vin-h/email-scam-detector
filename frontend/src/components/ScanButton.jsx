import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { AlertCircle, CheckCircle, Loader, Scan } from 'lucide-react';
import { api } from '../api/client.js';
import { isDemoMode } from '../hooks/useAuth.js';

const DEMO_SCAN_RESULT = {
  scanned: 12,
  new: 0,
  scams_found: 0,
};

export function ScanButton({ onComplete }) {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [popupPos, setPopupPos] = useState(null);
  const dismissRef = useRef(null);
  const buttonRef = useRef(null);

  useEffect(() => {
    if (!result && !error) return;
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setPopupPos({ top: rect.bottom + 10, right: window.innerWidth - rect.right });
    }
    clearTimeout(dismissRef.current);
    dismissRef.current = setTimeout(() => {
      setResult(null);
      setError(null);
      setPopupPos(null);
    }, 4000);
    return () => clearTimeout(dismissRef.current);
  }, [result, error]);

  const handleScan = async () => {
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      if (isDemoMode()) {
        setResult(DEMO_SCAN_RESULT);
        onComplete?.();
        return;
      }
      const data = await api.triggerScan();
      setResult(data);
      onComplete?.();
    } catch (err) {
      setError(err.message === 'NOT_AUTHENTICATED' ? 'Not signed in.' : 'Scan failed.');
    } finally {
      setScanning(false);
    }
  };

  const popup =
    (result || error) && popupPos
      ? createPortal(
          <div
            className="fixed z-[9999] w-56 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-xl shadow-slate-900/10 dark:shadow-slate-900/50 overflow-hidden"
            style={{ top: popupPos.top, right: popupPos.right }}
          >
            {result && (
              <div className="flex items-start gap-3 px-3.5 py-3">
                <CheckCircle size={16} strokeWidth={2} className="mt-0.5 shrink-0 text-emerald-500" />
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Scan complete</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {result.new} new ·{' '}
                    <span className="font-semibold text-rose-500 dark:text-rose-400">
                      {result.scams_found} scam{result.scams_found !== 1 ? 's' : ''}
                    </span>
                  </p>
                </div>
              </div>
            )}
            {error && (
              <div className="flex items-start gap-3 px-3.5 py-3">
                <AlertCircle size={16} strokeWidth={2} className="mt-0.5 shrink-0 text-rose-500" />
                <div>
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">Scan failed</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{error}</p>
                </div>
              </div>
            )}
          </div>,
          document.body
        )
      : null;

  return (
    <div className="shrink-0">
      <div className="relative inline-flex" ref={buttonRef}>
        {scanning && (
          <span className="absolute inset-0 rounded-full bg-indigo-500/30 animate-ping" aria-hidden="true" />
        )}
        <button
          onClick={handleScan}
          disabled={scanning}
          className="relative inline-flex items-center gap-2 px-5 py-2.5 rounded-full font-semibold text-sm text-white bg-gradient-to-br from-indigo-500 to-violet-600 shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 active:scale-95 transition-all disabled:opacity-70 disabled:cursor-not-allowed"
        >
          {scanning
            ? <Loader size={15} strokeWidth={2.5} className="animate-spin" />
            : <Scan size={15} strokeWidth={2} />}
          {scanning ? 'Scanning…' : 'Scan Now'}
        </button>
      </div>
      {popup}
    </div>
  );
}
