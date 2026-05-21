import { useState } from 'react';
import { Loader, Scan } from 'lucide-react';
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
      setError(err.message === 'NOT_AUTHENTICATED' ? 'Not signed in.' : 'Scan failed.');
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-2 shrink-0">
      <div className="relative inline-flex">
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
      {result && (
        <p className="text-xs text-slate-600">
          {result.new} new ·{' '}
          <span className="text-rose-600 font-semibold">
            {result.scams_found} scam{result.scams_found !== 1 ? 's' : ''}
          </span>
        </p>
      )}
      {error && <p className="text-xs text-rose-600">{error}</p>}
    </div>
  );
}
