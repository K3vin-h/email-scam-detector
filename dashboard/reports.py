from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from dashboard.models import EmailRecord, SummaryReport
from dashboard.risk import RISK_SCAM, risk_level_for_email


_REPORT_WINDOWS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}


def generate_summary_reports() -> list[SummaryReport]:
    """Create current daily, weekly, and monthly scam summary snapshots."""
    now = timezone.now()
    reports: list[SummaryReport] = []
    SummaryReport.objects.filter(period__in=_REPORT_WINDOWS).delete()

    for period, window in _REPORT_WINDOWS.items():
        since = now - window
        scam_ids = [
            record.id
            for record in EmailRecord.objects.filter(scanned_at__gte=since)
            if risk_level_for_email(
                sender=record.sender,
                confidence=record.confidence,
                is_scam=record.is_scam,
                user_risk_override=record.user_risk_override,
            ) == RISK_SCAM
        ]
        scam_qs = EmailRecord.objects.filter(id__in=scam_ids)
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
