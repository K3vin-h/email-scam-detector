# Background Scheduler and Reports

## Jobs

`dashboard/scheduler.py` runs three `APScheduler` `BackgroundScheduler` jobs, keyed by stable IDs so they can be rescheduled in place without restarting the scheduler:

| Job ID | Trigger | Function |
|---|---|---|
| `background_scan` | `IntervalTrigger(hours=scan_frequency_hours)` | `run_scan()` |
| `settings_sync` | Every 60s | Detects `ScanSettings` changes, calls `reschedule_scan`/`reschedule_report_job` |
| `report_generation` | Hours derived from `notify_frequency` (24/168/720) | Generates + optionally emails a report |

## Concurrency control — two locks, two failure modes

- **`threading.Lock()`** — serializes `start_scheduler()` against double-invocation from multiple threads within one process (e.g. a threaded WSGI server).
- **`fcntl.flock(..., LOCK_EX | LOCK_NB)`** on a lock file (path overridable via `SCAM_FILTER_SCHEDULER_LOCK_FILE`) — an OS-level, cross-process lock. In a multi-worker deployment (e.g. `gunicorn --workers N`), only the worker that acquires the file lock actually starts a scheduler; the rest no-op. `fcntl` is unavailable on Windows; the module degrades to a logged warning rather than raising.

These are independent because a thread lock has no visibility across process boundaries, and a file lock is unnecessary overhead within a single already-serialized process.

## Circuit breaker

`_run_scan_job` tracks `_consecutive_failures` (module-level). After `MAX_CONSECUTIVE_FAILURES = 3`, the job is paused via `scheduler.pause_job(SCAN_JOB_ID)` and a `critical`-level log is emitted. Any single success resets the counter. This bounds the failure mode of a permanently invalid state (e.g. a revoked OAuth token) to three attempts rather than indefinite retries against a dead credential.

## Cross-process settings propagation

Because only one process owns the running scheduler, and settings can be changed via any process serving the API, `settings_sync` polls `ScanSettings` every 60 seconds and calls `reschedule_job()` when the persisted value diverges from the scheduler's in-memory state — a polling-based eventual-consistency mechanism rather than a push notification. `_clamp_hours()` enforces `[1, 168]` independent of `ScanSettingsSerializer`'s validation, as a second line of defense against a zero/negative interval reaching `IntervalTrigger`.

## Reports (`dashboard/reports.py`, `dashboard/email_report.py`)

`generate_summary_reports()` wraps delete-and-recreate for the target period(s) in `transaction.atomic()`, so a report read never observes a partially-replaced state. `send_summary_email()` builds text and HTML alternatives (`EmailMultiAlternatives`); all interpolated user data (sender addresses) is passed through `html.escape()` before insertion into the HTML body. `EMAIL_BACKEND` defaults to Django's console backend in development — no SMTP credentials required to exercise the code path locally (`python manage.py generate_report --dry-run`).

## See also

- [02-django-backend.md](02-django-backend.md) — `ScanSettings`, `SummaryReport` schema
- [07-limitations.md](07-limitations.md) — polling latency, alerting gaps
