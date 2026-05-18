from django.core.management.base import BaseCommand

from dashboard.scanner import run_scan


class Command(BaseCommand):
    help = "Scan recent Gmail messages for scams and persist results."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and classify emails but do not save results or apply Gmail labels.",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write("Dry-run mode — no data will be saved.\n")

        self.stdout.write("Starting Gmail scan...\n")

        try:
            result = run_scan(dry_run=options["dry_run"])
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Scan failed: {exc}\n"))
            raise SystemExit(1)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Fetched {result['scanned']} emails — "
                f"{result['new']} new, {result['scams_found']} scams detected.\n"
            )
        )
