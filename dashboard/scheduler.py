"""
Background scheduler for automatic Gmail scans.

Uses APScheduler 3.x BackgroundScheduler to call run_scan() on a
configurable interval driven by ScanSettings.scan_frequency_hours.

The scheduler is a module-level singleton started once at Django boot
(via apps.py ready()). It runs in a daemon thread and shuts down
automatically when the process exits via APScheduler's atexit hook.
"""
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

try:
    import fcntl
except ImportError:  # pragma: no cover - fcntl is unavailable on Windows
    fcntl = None

logger = logging.getLogger(__name__)

# One scheduler per process - created in start_scheduler(), reused everywhere
_scheduler: Optional[BackgroundScheduler] = None
_scheduler_lock_file: Optional[object] = None

# Lock prevents double-start under threaded WSGI servers (e.g. gunicorn --threads N)
_scheduler_lock = threading.Lock()

# File lock prevents duplicate scheduler ownership across worker processes.
SCHEDULER_LOCK_FILE_ENV = "SCAM_FILTER_SCHEDULER_LOCK_FILE"

# Stable job IDs so we can reschedule without restarting the scheduler
SCAN_JOB_ID = "background_scan"
SETTINGS_SYNC_JOB_ID = "settings_sync"
REPORT_JOB_ID = "report_generation"
SETTINGS_SYNC_INTERVAL_SECONDS = 60

# Interval bounds — enforced here independently of model-layer validation
# so a zero-interval bug can never cause a runaway scan loop
MIN_INTERVAL_HOURS = 1
MAX_INTERVAL_HOURS = 168  # 1 week

# Maps ScanSettings.notify_frequency choices to hours for the report job trigger
_NOTIFY_FREQUENCY_TO_HOURS: dict[str, int] = {
    "daily": 24,
    "weekly": 168,
    "monthly": 720,
}

# Circuit breaker: pause the scheduler after this many consecutive failures
# so a permanently broken OAuth token does not spam logs endlessly
MAX_CONSECUTIVE_FAILURES = 3
_consecutive_failures = 0
_current_interval_hours: Optional[int] = None
_current_notify_frequency: Optional[str] = None


def _scheduler_lock_path() -> Path:
    """Return the inter-process lock file path."""
    configured_path = os.environ.get(SCHEDULER_LOCK_FILE_ENV)
    if configured_path:
        return Path(configured_path)
    return Path(tempfile.gettempdir()) / "scam-filter-background-scheduler.lock"


def _acquire_process_lock() -> bool:
    """Acquire the non-blocking process lock for the scheduler owner."""
    global _scheduler_lock_file

    if fcntl is None:
        logger.warning(
            "fcntl is unavailable; scheduler cannot enforce an inter-process lock"
        )
        return False

    lock_path = _scheduler_lock_path()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = lock_path.open("w")

    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_file.close()
        logger.info(
            "Background scheduler already owned by another process; skipping start"
        )
        return False

    lock_file.seek(0)
    lock_file.truncate()
    lock_file.write(str(os.getpid()))
    lock_file.flush()
    _scheduler_lock_file = lock_file
    return True


def _release_process_lock() -> None:
    """Release the scheduler process lock if this process owns it."""
    global _scheduler_lock_file

    if _scheduler_lock_file is None:
        return

    try:
        if fcntl is not None:
            fcntl.flock(_scheduler_lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        _scheduler_lock_file.close()
        _scheduler_lock_file = None


def _clamp_hours(hours: int) -> int:
    """Clamp a raw interval value to the safe operating range."""
    return max(MIN_INTERVAL_HOURS, min(hours, MAX_INTERVAL_HOURS))


def _load_scan_frequency_hours(default: int = 6) -> int:
    """Read the persisted scan interval, falling back when the DB is unavailable."""
    from django.db import OperationalError, ProgrammingError
    from dashboard.models import ScanSettings

    try:
        settings_obj = ScanSettings.objects.get(pk=1)
        return _clamp_hours(settings_obj.scan_frequency_hours)
    except (ScanSettings.DoesNotExist, OperationalError, ProgrammingError):
        return _clamp_hours(default)


def _load_notify_frequency(default: str = "weekly") -> str:
    """Read the persisted notification frequency, falling back when DB is unavailable."""
    from django.db import OperationalError, ProgrammingError
    from dashboard.models import ScanSettings

    try:
        settings_obj = ScanSettings.objects.get(pk=1)
        return settings_obj.notify_frequency
    except (ScanSettings.DoesNotExist, OperationalError, ProgrammingError):
        return default


def _sync_scan_settings() -> None:
    """Poll persisted settings so the scheduler owner sees cross-process changes."""
    global _current_interval_hours, _current_notify_frequency

    if _scheduler is None:
        return

    hours = _load_scan_frequency_hours(default=_current_interval_hours or 6)
    if hours != _current_interval_hours:
        logger.info(
            "Detected scan frequency change: %s -> %d hour(s)",
            _current_interval_hours,
            hours,
        )
        reschedule_scan(hours)

    frequency = _load_notify_frequency(default=_current_notify_frequency or "weekly")
    if frequency != _current_notify_frequency:
        logger.info(
            "Detected notify frequency change: %s -> %s",
            _current_notify_frequency,
            frequency,
        )
        reschedule_report_job(frequency)


def _run_scan_job() -> None:
    """Job function called by APScheduler on each interval tick.

    Distinguishes transient failures (log + continue) from repeated
    consecutive failures (log critical + pause the job via circuit breaker).
    Exceptions are never propagated so the scheduler thread stays alive.
    """
    global _consecutive_failures

    # Late import to avoid circular dependency at module load time
    from dashboard.scanner import run_scan

    try:
        result = run_scan()
        # Reset circuit breaker on success
        _consecutive_failures = 0
        logger.info("Background scan complete: %s", result)
    except Exception as exc:
        _consecutive_failures += 1
        logger.error(
            "Background scan failed (%d/%d consecutive): %s",
            _consecutive_failures,
            MAX_CONSECUTIVE_FAILURES,
            exc,
            exc_info=True,
        )
        if _consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            logger.critical(
                "Scan has failed %d times in a row — pausing background scheduler. "
                "Check Gmail OAuth token (token.json) and database connectivity.",
                _consecutive_failures,
            )
            if _scheduler is not None:
                # Pause so logs are not flooded; operator must investigate
                _scheduler.pause_job(SCAN_JOB_ID)


def _run_report_job() -> None:
    """Generate summary reports and email the one matching notify_frequency.

    Exceptions are caught and logged so the scheduler thread stays alive.
    Email is only sent if notify_via_email=True and notify_email_address is set.
    """
    from dashboard.email_report import send_summary_email
    from dashboard.models import ScanSettings
    from dashboard.reports import generate_summary_reports

    try:
        cfg = ScanSettings.load()
        reports = generate_summary_reports(period=cfg.notify_frequency)
        if cfg.notify_via_email and cfg.notify_email_address:
            target = next((r for r in reports if r.period == cfg.notify_frequency), None)
            if target is not None:
                send_summary_email(target, cfg.notify_email_address)
        logger.info(
            "Report generation job complete (%d %s report)",
            len(reports),
            cfg.notify_frequency,
        )
    except Exception as exc:
        logger.error("Report generation job failed: %s", exc, exc_info=True)


def start_scheduler(scan_frequency_hours: int) -> None:
    """Create and start the background scheduler.

    Idempotent: if the scheduler is already running this is a no-op.
    A threading lock prevents double-start under multi-threaded WSGI servers.
    A non-blocking file lock prevents separate worker processes from each
    running their own copy of the scheduled scan.
    APScheduler registers an atexit handler for graceful shutdown automatically.

    Args:
        scan_frequency_hours: How often to run the background scan.
                              Clamped to [1, 168] hours regardless of input.
    """
    global _scheduler, _current_interval_hours, _current_notify_frequency

    hours = _clamp_hours(scan_frequency_hours)

    with _scheduler_lock:
        if _scheduler is not None:
            logger.debug("Scheduler already running — skipping start")
            return

        if not _acquire_process_lock():
            return

        notify_frequency = _load_notify_frequency()
        report_hours = _NOTIFY_FREQUENCY_TO_HOURS.get(notify_frequency)
        if report_hours is None:
            logger.warning(
                "Unknown notify_frequency %r — defaulting report job to 24 hour(s)",
                notify_frequency,
            )
            report_hours = 24

        _scheduler = BackgroundScheduler(daemon=True)
        try:
            _scheduler.add_job(
                _run_scan_job,
                trigger=IntervalTrigger(hours=hours),
                id=SCAN_JOB_ID,
                replace_existing=True,
                max_instances=1,  # prevent scan overlap if one run is slow
            )
            _scheduler.add_job(
                _sync_scan_settings,
                trigger=IntervalTrigger(seconds=SETTINGS_SYNC_INTERVAL_SECONDS),
                id=SETTINGS_SYNC_JOB_ID,
                replace_existing=True,
                max_instances=1,
            )
            _scheduler.add_job(
                _run_report_job,
                trigger=IntervalTrigger(hours=report_hours),
                id=REPORT_JOB_ID,
                replace_existing=True,
                max_instances=1,
            )
            _scheduler.start()
            _current_interval_hours = hours
            _current_notify_frequency = notify_frequency
        except Exception:
            _scheduler = None
            _current_interval_hours = None
            _current_notify_frequency = None
            _release_process_lock()
            raise

    logger.info(
        "Background scheduler started — scanning every %d hour(s), "
        "reports every %d hour(s) (%s)",
        hours,
        report_hours,
        notify_frequency,
    )


def reschedule_scan(scan_frequency_hours: int) -> None:
    """Update the scan interval at runtime.

    Called via the post_save signal on ScanSettings whenever the user
    changes scan_frequency_hours in the settings page. Uses APScheduler's
    reschedule_job() so the scheduler itself is never restarted.

    No-ops if the scheduler has not been started yet (e.g. during tests
    or in the Django dev-server reloader process). The interval is clamped
    to [1, 168] hours to prevent runaway zero-interval loops.

    Args:
        scan_frequency_hours: New interval in hours.
    """
    global _current_interval_hours

    hours = _clamp_hours(scan_frequency_hours)

    if _scheduler is None:
        logger.debug("Scheduler not running — reschedule is a no-op")
        return

    if hours == _current_interval_hours:
        logger.debug("Scan interval already set to %d hour(s)", hours)
        return

    _scheduler.reschedule_job(
        SCAN_JOB_ID,
        trigger=IntervalTrigger(hours=hours),
    )
    _current_interval_hours = hours
    logger.info(
        "Rescheduled background scan to every %d hour(s)",
        hours,
    )


def reschedule_report_job(frequency: str) -> None:
    """Update the report generation interval to match a new notify_frequency.

    Called by _sync_scan_settings() when a cross-process settings change is
    detected. No-ops if the scheduler has not been started yet.

    Args:
        frequency: One of 'daily', 'weekly', 'monthly'.
    """
    global _current_notify_frequency

    if _scheduler is None:
        logger.debug("Scheduler not running — report reschedule is a no-op")
        return

    if frequency == _current_notify_frequency:
        logger.debug("Report frequency already set to %s", frequency)
        return

    report_hours = _NOTIFY_FREQUENCY_TO_HOURS.get(frequency)
    if report_hours is None:
        logger.warning(
            "Unknown notify_frequency %r — defaulting report job to 24 hour(s)", frequency
        )
        report_hours = 24
    _scheduler.reschedule_job(
        REPORT_JOB_ID,
        trigger=IntervalTrigger(hours=report_hours),
    )
    _current_notify_frequency = frequency
    logger.info(
        "Rescheduled report generation to every %d hour(s) (%s)",
        report_hours,
        frequency,
    )


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Return the active scheduler instance, or None if not yet started."""
    return _scheduler


def stop_scheduler(wait: bool = False) -> None:
    """Stop the active scheduler and release the process lock."""
    global _scheduler, _current_interval_hours, _current_notify_frequency

    try:
        if _scheduler is not None:
            _scheduler.shutdown(wait=wait)
    finally:
        _scheduler = None
        _current_interval_hours = None
        _current_notify_frequency = None
        _release_process_lock()
