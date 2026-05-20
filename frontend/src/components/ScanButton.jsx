import { useState } from 'react';
import { api } from '../api/client.js';

export function ScanButton({ onComplete }) {
  const [scanning, setScanning] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleScan = async () => {
    setScanning(true);
    setResult(null);
    setError(null);
    try {
      const data = await api.triggerScan();
      setResult(data);
      onComplete?.();
    } catch (err) {
      setError(
        err.message === 'NOT_AUTHENTICATED'
          ? 'Not signed in.'
          : 'Scan failed. Try again.'
      );
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <button
        onClick={handleScan}
        disabled={scanning}
        className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
      >
        {scanning && (
          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {scanning ? 'Scanning…' : 'Scan Now'}
      </button>
      {result && (
        <p className="text-sm text-slate-600">
          Scanned {result.new} new ·{' '}
          <span className="text-rose-600 font-medium">{result.scams_found} scam{result.scams_found !== 1 ? 's' : ''}</span>
        </p>
      )}
      {error && <p className="text-sm text-rose-600">{error}</p>}
    </div>
  );
}
