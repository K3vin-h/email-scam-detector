"""
Core scan logic — fetch Gmail messages, classify with ML, persist results.

Kept in its own module so it can be called from three places without duplication:
  - POST /api/scan/  (on-demand via the React dashboard)
  - manage.py scan_emails  (CLI / cron)
  - APScheduler background job (Phase 9)
"""

import logging
from datetime import datetime, timezone as dt_timezone

from dashboard.models import EmailRecord, ScanSettings
from gmail.fetch import get_email, list_emails
from gmail.labels import apply_label, get_or_create_label
from ml.predict import predict

logger = logging.getLogger(__name__)

_SCAM_LABEL_NAME = "Scam"


def run_scan(*, dry_run: bool = False) -> dict:
    """
    Fetch recent Gmail messages, classify each, and persist new results.

    Emails already in the database (by gmail_id) are skipped so re-runs
    are safe and don't produce duplicate records.

    Returns a summary: {"scanned": N, "new": N, "scams_found": N}.

    When dry_run=True, Gmail messages are fetched and classified but no
    EmailRecord rows are saved and no Gmail labels are created or applied.
    """
    settings = ScanSettings.load()
    # Heuristic: fetch ~10 emails per day in the scan window, capped by the API limit.
    max_results = min(settings.scan_window_days * 10, 50)

    emails = list_emails(max_results=max_results)

    # Resolve the Gmail label ID once — avoids one API call per scam email.
    scam_label_id: str | None = None

    new_count = 0
    scams_found = 0

    for meta in emails:
        gmail_id = meta["id"]

        if EmailRecord.objects.filter(gmail_id=gmail_id).exists():
            continue

        try:
            email = get_email(gmail_id)
        except Exception:
            logger.exception("Failed to fetch Gmail message %s — skipping", gmail_id)
            continue

        text = email.get("body") or email.get("snippet", "")
        is_scam, confidence = predict(text)

        received_at = email.get("received_at") or datetime.now(tz=dt_timezone.utc)

        if dry_run:
            new_count += 1
            if is_scam:
                scams_found += 1
            continue

        record = EmailRecord(
            gmail_id=gmail_id,
            sender=email["sender"],
            subject=email["subject"],
            snippet=email["snippet"],
            received_at=received_at,
            confidence=confidence,
            is_scam=is_scam,
            labeled_in_gmail=False,
        )

        if is_scam:
            try:
                if scam_label_id is None:
                    scam_label_id = get_or_create_label(_SCAM_LABEL_NAME)
                apply_label(gmail_id, scam_label_id)
                record.labeled_in_gmail = True
            except Exception:
                logger.exception("Failed to apply Gmail label to message %s", gmail_id)
            scams_found += 1

        record.save()
        new_count += 1

    return {"scanned": len(emails), "new": new_count, "scams_found": scams_found}
