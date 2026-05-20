function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

export function EmailRow({ email }) {
  const pct = Math.round(email.confidence * 100);

  return (
    <tr className="hover:bg-slate-50 transition-colors">
      <td className="px-4 py-3 max-w-[180px]">
        <p className="text-sm font-medium text-slate-900 truncate">{email.sender}</p>
      </td>
      <td className="px-4 py-3 max-w-xs">
        <p className="text-sm text-slate-700 truncate">{email.subject}</p>
        <p className="text-xs text-slate-400 truncate mt-0.5">{email.snippet}</p>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            email.is_scam
              ? 'bg-rose-50 text-rose-700'
              : 'bg-emerald-50 text-emerald-700'
          }`}
        >
          {email.is_scam ? 'Scam' : 'Legit'}
        </span>
      </td>
      <td className="px-4 py-3 whitespace-nowrap">
        <div className="flex items-center gap-2">
          <div className="w-14 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${email.is_scam ? 'bg-rose-500' : 'bg-emerald-500'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className="text-xs tabular-nums text-slate-500">{pct}%</span>
        </div>
      </td>
      <td className="px-4 py-3 whitespace-nowrap text-xs text-slate-400">
        {formatDate(email.received_at)}
      </td>
    </tr>
  );
}
