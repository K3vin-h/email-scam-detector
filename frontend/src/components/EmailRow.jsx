function formatDate(iso) {
  const date = new Date(iso);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getInitials(sender) {
  const name = (sender.split('@')[0] ?? '').replace(/[._-]/g, ' ').trim();
  return name.split(' ').map(w => w[0]?.toUpperCase() ?? '').filter(Boolean).slice(0, 2).join('') || '?';
}

export function EmailRow({ email }) {
  const pct = Math.round(email.confidence * 100);
  const reasons = Array.isArray(email.reasons) ? email.reasons : [];
  const tone = email.is_scam
    ? {
        border: 'border-l-rose-500',
        badge: 'bg-rose-50 text-rose-700 border-rose-200',
        bar: 'bg-rose-500',
        chip: 'bg-rose-50/80 text-rose-700 border-rose-200/80',
      }
    : {
        border: 'border-l-emerald-500',
        badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        bar: 'bg-emerald-500',
        chip: 'bg-emerald-50/80 text-emerald-700 border-emerald-200/80',
      };

  return (
    <div className={`group flex items-start gap-3 sm:gap-4 px-4 py-3.5 border-l-4 bg-white/60 backdrop-blur-sm transition-colors hover:bg-white/90 ${tone.border}`}>
      <div className="shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center mt-0.5 select-none">
        {getInitials(email.sender)}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-slate-900 truncate flex-1">{email.subject}</p>
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border shrink-0 ${tone.badge}`}>
            {email.is_scam ? 'Scam' : 'Legit'}
          </span>
          <span className="text-xs text-slate-400 tabular-nums shrink-0">{formatDate(email.received_at)}</span>
        </div>
        <p className="text-xs text-slate-500 truncate mt-1">
          <span className="font-medium text-slate-600">{email.sender}</span>
          <span className="hidden sm:inline text-slate-400"> — {email.snippet}</span>
        </p>
        <div className="flex flex-wrap items-center gap-2 mt-2">
          {reasons.map((r) => (
            <span key={r} className={`text-[10px] font-medium px-2 py-0.5 rounded-md border ${tone.chip}`}>
              {r}
            </span>
          ))}
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${tone.bar}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-[10px] tabular-nums text-slate-500">{pct}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
