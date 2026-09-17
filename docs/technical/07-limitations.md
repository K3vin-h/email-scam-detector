# Known Limitations

## Data layer

- **SQLite** is appropriate for a single-user, locally-run deployment but not for concurrent multi-writer or multi-tenant use. Migrating to Postgres would be the first step toward either.
- **Risk-level filtering is computed in Python, not SQL.** `EmailListView`, `StatsView`, `DailyStatsView`, and `TopSendersView` iterate the full `EmailRecord` table to evaluate `risk_level_for_email()` per row, since risk level is not a stored column. This is O(n) per filtered request. A denormalized `risk_level` column (recomputed on write) or an equivalent query-level annotation would remove this bottleneck at scale.

## Model

- TF-IDF has no representation of word order or semantics — lexically similar but semantically opposite phrasing can produce near-identical feature vectors. A contextual embedding model would address this at materially higher compute cost.
- No feedback loop exists between manual risk corrections and model retraining; corrections affect only display state (`user_risk_override`), never the underlying weights or thresholds.
- `SCAM_THRESHOLD` (`ml/predict.py`) and `POSSIBLE_SCAM_THRESHOLD` (`dashboard/risk.py`) are independent constants in separate modules with no shared source of truth or test asserting their relative ordering.
- `TRUSTED_LEGIT_DOMAINS` is a hardcoded allowlist, not user-configurable; extending it requires a code change and redeploy rather than a settings update.

## OAuth / Gmail integration

- Tokens are stored in a single flat file (`token.json`) rather than a keychain or secrets manager — acceptable for single-user local deployment, not appropriate for multi-user hosting.
- No retry/backoff on Gmail API calls; a transient failure during `fetch`/`labels` is logged and the affected message is skipped until the next scan.

## Scheduler

- Cross-process settings propagation (`settings_sync`) is polling-based with up to 60 seconds of propagation latency, rather than push-based.
- The circuit breaker (`MAX_CONSECUTIVE_FAILURES`) only pauses the scan job; the report-generation job continues running independently and is not covered by the same failure-detection logic.
- Failure signaling is log-only (`logger.critical`); no external alerting (push/email) on circuit-breaker trip.

## Frontend

- No centralized state store; each hook (`useEmails`, `useStats`, `useReports`) independently implements fetch/loading/refresh logic.
- Optimistic UI updates (risk corrections) have no explicit rollback on request failure — reconciliation happens only on the next background refetch.
- Demo-mode branching (`isDemoMode()`) is duplicated per hook rather than centralized behind a single API-layer seam.
