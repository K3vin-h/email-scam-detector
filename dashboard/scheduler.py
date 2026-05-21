"""
Background scheduler for automatic Gmail scans.

Uses APScheduler 3.x BackgroundScheduler to call run_scan() on a
configurable interval driven by ScanSettings.scan_frequency_hours.

The scheduler is a module-level singleton started once at Django boot
(via apps.py ready()). It runs in a daemon thread and shuts down
automatically when the process exits via APScheduler's atexit hook.
"""
import logging
import threading
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# One scheduler per process — created in start_scheduler(), reused everywhere
_scheduler: Optional[BackgroundScheduler] = None

# Lock prevents double-start under threaded WSGI servers (e.g. gunicorn --threads N)
_scheduler_lock = threading.Lock()

# Stable job ID so we can reschedule without restarting the scheduler
SCAN_JOB_ID = "background_scan"

# Interval bounds — enforced here independently of model-layer validation
# so a zero-interval bug can never cause a runaway scan loop
MIN_INTERVAL_HOURS = 1
MAX_INTERVAL_HOURS = 168  # 1 week

# Circuit breaker: pause the scheduler after this many consecutive failures
# so a permanently broken OAuth token does not spam logs endlessly
MAX_CONSECUTIVE_FAILURES = 3
_consecutive_failures = 0


def _clamp_hours(hours: int) -> int:
    """Clamp a raw interval value to the safe operating range."""
    return max(MIN_INTERVAL_HOURS, min(hours, MAX_INTERVAL_HOURS))


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


def start_scheduler(scan_frequency_hours: int) -> None:
    """Create and start the background scheduler.

    Idempotent: if the scheduler is already running this is a no-op.
    A threading lock prevents double-start under multi-threaded WSGI servers.
    APScheduler registers an atexit handler for graceful shutdown automatically.

    Args:
        scan_frequency_hours: How often to run the background scan.
                              Clamped to [1, 168] hours regardless of input.
    """
    global _scheduler

    hours = _clamp_hours(scan_frequency_hours)

    with _scheduler_lock:
        if _scheduler is not None:
            logger.debug("Scheduler already running — skipping start")
            return

        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(
            _run_scan_job,
            trigger=IntervalTrigger(hours=hours),
            id=SCAN_JOB_ID,
            replace_existing=True,
            max_instances=1,  # prevent scan overlap if one run is slow
        )
        _scheduler.start()

    logger.info(
        "Background scheduler started — scanning every %d hour(s)",
        hours,
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
    hours = _clamp_hours(scan_frequency_hours)

    if _scheduler is None:
        logger.debug("Scheduler not running — reschedule is a no-op")
        return

    _scheduler.reschedule_job(
        SCAN_JOB_ID,
        trigger=IntervalTrigger(hours=hours),
    )
    logger.info(
        "Rescheduled background scan to every %d hour(s)",
        hours,
    )


def get_scheduler() -> Optional[BackgroundScheduler]:
    """Return the active scheduler instance, or None if not yet started."""
    return _scheduler
