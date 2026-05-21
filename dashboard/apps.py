"""
Django AppConfig for the dashboard app.

The ready() hook wires two things at startup:
  1. A post_save signal on ScanSettings so the scheduler interval is
     updated whenever the user changes scan_frequency_hours.
  2. The APScheduler background thread only for the Django dev server child
     process, or when explicitly enabled via environment variable.
"""
import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)
SCHEDULER_AUTOSTART_ENV = "SCAM_FILTER_AUTO_START_SCHEDULER"


def _env_flag_enabled(name: str) -> bool:
    return os.environ.get(name, "").lower() in {"1", "true", "yes", "on"}


def _should_start_scheduler() -> bool:
    """Return whether this Django process should start APScheduler."""
    if "test" in sys.argv or "pytest" in sys.modules:
        return False

    if _env_flag_enabled(SCHEDULER_AUTOSTART_ENV):
        return True

    running_dev_server = "runserver" in sys.argv
    if not running_dev_server:
        return False

    return os.environ.get("RUN_MAIN") == "true" or "--noreload" in sys.argv


def _reschedule_handler(sender, instance, **kwargs) -> None:
    """Signal handler: reschedule the background scan when settings change.

    Connected to ScanSettings post_save in DashboardConfig.ready().
    Importing reschedule_scan here (not at module level) avoids circular
    imports because apps.py is loaded before the rest of the dashboard app.
    """
    from dashboard.scheduler import reschedule_scan

    reschedule_scan(instance.scan_frequency_hours)


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self) -> None:
        """Called once by Django after the app registry is fully populated.

        Connects the ScanSettings signal and conditionally starts the
        APScheduler background thread.
        """
        from django.db.models.signals import post_save
        from dashboard.models import ScanSettings

        # dispatch_uid prevents duplicate signal registration if ready() is
        # ever called more than once (e.g. some test configurations).
        post_save.connect(
            _reschedule_handler,
            sender=ScanSettings,
            weak=False,
            dispatch_uid="dashboard.apps.reschedule_on_settings_save",
        )

        if not _should_start_scheduler():
            logger.debug("Skipping scheduler start for this process")
            return

        # Read the persisted interval; fall back to the model default (6h)
        # if ScanSettings has never been saved (fresh install) or if
        # migrations have not been applied yet (OperationalError / ProgrammingError).
        from django.db import OperationalError, ProgrammingError

        try:
            settings_obj = ScanSettings.objects.get(pk=1)
            hours = settings_obj.scan_frequency_hours
        except (ScanSettings.DoesNotExist, OperationalError, ProgrammingError):
            hours = 6

        from dashboard.scheduler import start_scheduler

        start_scheduler(hours)
