function getCsrfToken() {
  return document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? '';
}

async function request(path, { method = 'GET', body, ...opts } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['X-CSRFToken'] = getCsrfToken();
  }
  const res = await fetch(path, {
    method,
    credentials: 'include',
    headers,
    body: body != null ? JSON.stringify(body) : undefined,
    ...opts,
  });
  if (res.status === 401 || res.status === 403) {
    throw Object.assign(new Error('NOT_AUTHENTICATED'), { status: res.status });
  }
  if (!res.ok) {
    throw Object.assign(new Error(`HTTP_${res.status}`), { status: res.status });
  }
  return res.status === 204 ? null : res.json();
}

export const api = {
  getHealth:      ()       => request('/api/health/'),
  getEmails:      (params) => request(`/api/emails/?${new URLSearchParams(params)}`),
  getStats:       ()       => request('/api/stats/'),
  getDailyStats:  ()       => request('/api/stats/daily/'),
  getSenderStats: ()       => request('/api/stats/senders/'),
  getSettings:    ()       => request('/api/settings/'),
  patchSettings:  (data)   => request('/api/settings/', { method: 'PATCH', body: data }),
  getReports:     (period) => request(`/api/reports/${period ? `?${new URLSearchParams({ period })}` : ''}`),
  triggerScan:    ()       => request('/api/scan/', { method: 'POST' }),
  correctEmailRisk: (id, riskLevel) => request(`/api/emails/${id}/risk/`, { method: 'PATCH', body: { risk_level: riskLevel } }),
};
