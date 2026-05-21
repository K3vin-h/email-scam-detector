from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from dashboard.models import EmailRecord, SummaryReport


_REPORT_WINDOWS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}


def generate_summary_reports() -> list[SummaryReport]:
    """Create current daily, weekly, and monthly scam summary snapshots."""
    now = timezone.now()
    reports: list[SummaryReport] = []

    for period, window in _REPORT_WINDOWS.items():
        since = now - window
        scam_qs = EmailRecord.objects.filter(is_scam=True, scanned_at__gte=since)
        top_senders = list(
            scam_qs.values("sender")
            .annotate(count=Count("id"))
            .order_by("-count", "sender")[:5]
        )
        reports.append(
            SummaryReport.objects.create(
                period=period,
                total_scams=scam_qs.count(),
                top_senders=top_senders,
            )
        )

    return reports


def ensure_summary_reports() -> None:
    """Backfill report snapshots so the reports page has data after scans."""
    if EmailRecord.objects.exists() and not SummaryReport.objects.exists():
        generate_summary_reports()
