import { ChevronLeft, ChevronRight } from 'lucide-react';

export function Pagination({ page, count, pageSize = 50, onPageChange }) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-center gap-3 px-4 py-5 border-t border-slate-200/70" role="navigation" aria-label="Pagination">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={!hasPrev}
        aria-label="Previous page"
        className="inline-flex items-center justify-center w-9 h-9 rounded-full border border-slate-200 bg-white/70 backdrop-blur-sm text-slate-600 hover:border-indigo-300 hover:text-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95 disabled:active:scale-100"
      >
        <ChevronLeft size={16} />
      </button>
      <span className="text-sm text-slate-500 tabular-nums">
        Page <span className="font-semibold text-slate-900">{page}</span> of <span className="font-semibold text-slate-900">{totalPages}</span>
      </span>
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={!hasNext}
        aria-label="Next page"
        className="inline-flex items-center justify-center w-9 h-9 rounded-full border border-slate-200 bg-white/70 backdrop-blur-sm text-slate-600 hover:border-indigo-300 hover:text-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all active:scale-95 disabled:active:scale-100"
      >
        <ChevronRight size={16} />
      </button>
    </div>
  );
}
