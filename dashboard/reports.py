from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from dashboard.models import EmailRecord, SummaryReport
from dashboard.risk import RISK_SCAM, risk_level_for_email


_REPORT_WINDOWS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=30),
}


def _build_summary_report(period: str, now) -> SummaryReport:
    """Create the current scam summary snapshot for one period."""
    window = _REPORT_WINDOWS[period]
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
    return SummaryReport.objects.create(
        period=period,
        total_scams=scam_qs.count(),
        top_senders=top_senders,
    )


def generate_summary_reports(period: str | None = None) -> list[SummaryReport]:
    """Create current scam summary snapshots.

    Args:
        period: Optional report period to generate. When omitted, generates
            daily, weekly, and monthly reports for dashboard backfill.
    """
    now = timezone.now()
    periods = [period] if period else list(_REPORT_WINDOWS)
    unknown_periods = [p for p in periods if p not in _REPORT_WINDOWS]
    if unknown_periods:
        raise ValueError(f"Unknown report period: {unknown_periods[0]}")

    with transaction.atomic():
        SummaryReport.objects.filter(period__in=periods).delete()
        return [_build_summary_report(p, now) for p in periods]


def ensure_summary_reports() -> None:
    """Backfill report snapshots so the reports page has data after scans."""
    if EmailRecord.objects.exists() and not SummaryReport.objects.exists():
        generate_summary_reports()
