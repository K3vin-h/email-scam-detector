"""Management command to manually generate summary reports and optionally send them."""
import logging

from django.core.management.base import BaseCommand

from dashboard.email_report import build_text_body, send_summary_email
from dashboard.models import ScanSettings
from dashboard.reports import generate_summary_reports

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Generate daily/weekly/monthly summary reports and send an email "
        "if notifications are enabled in Settings. Use --dry-run to preview "
        "the email body without sending."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Generate reports and print the email body to stdout; do not send.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]

        self.stdout.write("Generating summary reports…")
        reports = generate_summary_reports()
        self.stdout.write(self.style.SUCCESS(f"Generated {len(reports)} report(s)."))

        cfg = ScanSettings.load()
        target = next((r for r in reports if r.period == cfg.notify_frequency), None)

        if target is None:
            self.stdout.write(f"No {cfg.notify_frequency!r} report was generated.")
            return

        if dry_run:
            self.stdout.write(f"\n{'─' * 50}")
            self.stdout.write(f"Email preview (notify_frequency={cfg.notify_frequency!r})")
            self.stdout.write("─" * 50)
            self.stdout.write(build_text_body(target))
            self.stdout.write("─" * 50)
            return

        if not cfg.notify_via_email:
            self.stdout.write(
                "Email notifications are disabled. "
                "Enable them in Settings → Email Reports."
            )
            return

        if not cfg.notify_email_address:
            self.stdout.write(
                "No email address configured. "
                "Set one in Settings → Email Reports."
            )
            return

        try:
            send_summary_email(target, cfg.notify_email_address)
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f"Failed to send email: {type(exc).__name__}: {exc}")
            )
            logger.error("generate_report email send failed", exc_info=True)
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Report sent (period={cfg.notify_frequency!r})."
            )
        )
