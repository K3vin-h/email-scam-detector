"""
Django AppConfig for the dashboard app.

The ready() hook wires two things at startup:
  1. A post_save signal on ScanSettings so the scheduler interval is
     updated whenever the user changes scan_frequency_hours.
  2. The APScheduler background thread (skipped in the dev-server reloader
     process and during test runs to avoid spurious background activity).
"""
import logging
import os
import sys

from django.apps import AppConfig

logger = logging.getLogger(__name__)


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

        # Skip the scheduler thread in test runs (manage.py test / pytest)
        # so background threads do not interfere with test isolation.
        if "test" in sys.argv or "pytest" in sys.modules:
            logger.debug("Skipping scheduler start in test environment")
            return

        # Django's dev server (manage.py runserver --reload) spawns two
        # processes.  Only the child process sets RUN_MAIN="true"; the
        # parent reloader process should not start the scheduler.
        # In production (gunicorn/uvicorn), RUN_MAIN is never set, so the
        # scheduler always starts there.
        running_dev_server = "runserver" in sys.argv
        is_reloader_process = running_dev_server and os.environ.get("RUN_MAIN") != "true"

        if is_reloader_process:
            logger.debug("Skipping scheduler start in dev reloader process")
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
