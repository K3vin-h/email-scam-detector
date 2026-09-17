# Frontend

## Routing (`App.jsx`)

`ProtectedLayout` gates `/`, `/reports`, `/settings` behind `useAuth()` — session state is checked once at the layout level via `<Outlet />`, rather than per-page. `/login` is the only unprotected route.

## API client (`api/client.js`)

A thin `fetch` wrapper: `credentials: 'include'` for session cookies, `X-CSRFToken` header (read from the `csrftoken` cookie) attached to all mutating verbs, and 401/403 normalized to a distinguishable `NOT_AUTHENTICATED` error so callers can separate "session expired" from "server error" (see `useAuth` below). All API access is centralized through the exported `api` object — no direct `fetch` calls elsewhere in the codebase.

## Auth state (`hooks/useAuth.js`)

```js
.catch((err) => {
  if (err.status === 401 || err.status === 403 || err.message === 'NOT_AUTHENTICATED') {
    setAuthenticated(false);   // confirmed logged out
  } else {
    setAuthenticated(null);    // ambiguous — network/server error, not a logout signal
    setError(err.message);
  }
});
```

The three-state model (`true` / `false` / `null`) exists specifically to avoid treating a transient backend outage as a session expiry.

## Data hooks and the loading/refreshing split

`useEmails`, `useStats`, and siblings distinguish first-load (`loading`, full-page loading state) from subsequent fetches (`refreshing`, existing data stays rendered with a small indicator), tracked via a `useRef` flag (`loadedRef`) that persists across renders without triggering one. This is the mechanism behind the dashboard never blanking on a scan or correction after initial load.

## Optimistic updates

`DashboardPage.handleCorrectRisk` applies the risk correction to local state synchronously, then fires the API call and reconciles via `refetchStats`/`refetchEmails` on completion. There is no explicit rollback path if the API call fails — the UI relies on the next background refetch to correct any divergence (tracked in [07-limitations.md](07-limitations.md)).

## Demo mode

`isDemoMode()` (a `localStorage` flag) is checked independently inside each data hook; when set, hooks read from `demo/mockData.js` instead of calling the API. This allows the full dashboard to be explored without Gmail OAuth or a live backend connection.

## Theme persistence

`ThemeToggle` resolves theme in priority order: explicit `localStorage` choice → OS `prefers-color-scheme` → light. It subscribes to OS theme-change events but only applies them while no explicit user choice is stored, avoiding an unwanted override of a deliberate manual selection.

## Cross-page state

`UnsavedChangesContext` is a minimal React context (`{ active, onBlocked }`) used by the Settings page to signal in-progress edits to the rest of the app, avoiding prop-drilling the flag through the route tree.

## See also

- [02-django-backend.md](02-django-backend.md) — the API surface this layer consumes
- [07-limitations.md](07-limitations.md) — state-management and rollback gaps
