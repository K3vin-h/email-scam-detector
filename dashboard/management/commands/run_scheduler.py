import threading

from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, ProgrammingError

from dashboard.models import ScanSettings
from dashboard.scheduler import get_scheduler, start_scheduler, stop_scheduler


class Command(BaseCommand):
    help = "Run the background scan scheduler as a dedicated process."

    def handle(self, *args, **options):
        try:
            settings_obj = ScanSettings.objects.get(pk=1)
            hours = settings_obj.scan_frequency_hours
        except (ScanSettings.DoesNotExist, OperationalError, ProgrammingError):
            hours = 6

        self.stdout.write(
            self.style.SUCCESS(
                f"Starting background scheduler; scanning every {hours} hour(s)."
            )
        )
        start_scheduler(hours)
        if get_scheduler() is None:
            raise CommandError("Another process already owns the background scheduler.")

        stop_event = threading.Event()
        try:
            while not stop_event.wait(3600):
                pass
        except KeyboardInterrupt:
            self.stdout.write("\nStopping background scheduler.")
        finally:
            stop_scheduler(wait=False)
