"""
Core scan logic — fetch Gmail messages, classify with ML, persist results.

Kept in its own module so it can be called from three places without duplication:
  - POST /api/scan/  (on-demand via the React dashboard)
  - manage.py scan_emails  (CLI / cron)
  - APScheduler background job (Phase 9)
"""

import logging
from datetime import datetime, timedelta, timezone as dt_timezone

from dashboard.models import EmailRecord, ScanSettings
from dashboard.reports import generate_summary_reports
from dashboard.risk import RISK_SCAM, risk_level_for_email
from gmail.fetch import get_email, list_email_ids
from gmail.labels import apply_label, get_or_create_label
from ml.predict import load_predictor

logger = logging.getLogger(__name__)

_SCAM_LABEL_NAME = "Scam"

_TRUSTED_BRANDS = [
    "amazon", "paypal", "google", "apple", "microsoft",
    "netflix", "irs", "usps", "fedex",
]
_URGENCY_WORDS = ["urgent", "immediately", "expire", "24 hours", "suspended", "final notice", "act now"]
_CREDENTIAL_WORDS = ["password", "verify your account", "credentials", "log in", "login"]
_CASH_WORDS = ["gift card", "won", "prize", "reward", "lottery", "congratulations"]
_CRYPTO_WORDS = ["bitcoin", "crypto", "nft", "airdrop", "investment opportunity", "trading bot"]
_SUSPICIOUS_TLDS = [".cc", ".shop", ".xyz", ".ru", ".tk", "bit.ly", "tinyurl"]


def _extract_reasons(text: str, sender: str) -> list[str]:
    """Return up to 4 rule-based tags explaining why an email looks like a scam."""
    reasons: list[str] = []
    text_lower = text.lower()
    domain = sender.lower().split("@")[-1] if "@" in sender else sender.lower()

    if any(w in text_lower for w in _URGENCY_WORDS):
        reasons.append("Urgency tactic")

    if any(w in text_lower for w in _CREDENTIAL_WORDS):
        reasons.append("Credential request")

    if any(w in text_lower for w in _CASH_WORDS):
        reasons.append("Cash incentive")

    for brand in _TRUSTED_BRANDS:
        if brand in domain and f"{brand}.com" not in domain and f"{brand}.gov" not in domain:
            reasons.append("Lookalike domain")
            break

    if "http" in text_lower and any(t in text_lower for t in _SUSPICIOUS_TLDS):
        reasons.append("Suspicious link")

    if any(w in text_lower for w in _CRYPTO_WORDS):
        reasons.append("Crypto/investment")

    return reasons[:4]


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
    cutoff = datetime.now(tz=dt_timezone.utc) - timedelta(days=settings.scan_window_days)
    gmail_query = f"after:{cutoff:%Y/%m/%d}"

    gmail_ids = list_email_ids(max_results=None, query=gmail_query)
    existing_records = EmailRecord.objects.in_bulk(gmail_ids, field_name="gmail_id")

    # Resolve the Gmail label ID once — avoids one API call per scam email.
    scam_label_id: str | None = None
    predict_email = None

    new_count = 0
    scams_found = 0

    for gmail_id in gmail_ids:
        existing_record = existing_records.get(gmail_id)
        if existing_record:
            should_label_existing = (
                risk_level_for_email(
                    sender=existing_record.sender,
                    confidence=existing_record.confidence,
                    is_scam=existing_record.is_scam,
                    user_risk_override=existing_record.user_risk_override,
                ) == RISK_SCAM
                and not existing_record.labeled_in_gmail
                and not dry_run
            )
            if should_label_existing:
                try:
                    if scam_label_id is None:
                        scam_label_id = get_or_create_label(_SCAM_LABEL_NAME)
                    apply_label(gmail_id, scam_label_id)
                    existing_record.labeled_in_gmail = True
                    existing_record.save(update_fields=["labeled_in_gmail"])
                except Exception:
                    logger.exception("Failed to apply Gmail label to message %s", gmail_id)
            continue

        try:
            email = get_email(gmail_id)
        except Exception:
            logger.exception("Failed to fetch Gmail message %s — skipping", gmail_id)
            continue

        text = email.get("body") or email.get("snippet", "")
        received_at = email.get("received_at") or datetime.now(tz=dt_timezone.utc)
        if received_at < cutoff:
            continue

        if predict_email is None:
            predict_email = load_predictor()
        model_is_scam, confidence = predict_email(text)
        risk_level = risk_level_for_email(
            sender=email["sender"],
            confidence=confidence,
            is_scam=model_is_scam,
        )
        is_scam = risk_level == RISK_SCAM

        if dry_run:
            new_count += 1
            if is_scam:
                scams_found += 1
            continue

        reasons = _extract_reasons(text, email["sender"]) if is_scam else []

        record, created = EmailRecord.objects.get_or_create(
            gmail_id=gmail_id,
            defaults={
                "sender": email["sender"],
                "subject": email["subject"],
                "snippet": email["snippet"],
                "received_at": received_at,
                "confidence": confidence,
                "is_scam": is_scam,
                "labeled_in_gmail": False,
                "reasons": reasons,
            },
        )
        if not created:
            continue

        if is_scam:
            try:
                if scam_label_id is None:
                    scam_label_id = get_or_create_label(_SCAM_LABEL_NAME)
                apply_label(gmail_id, scam_label_id)
                record.labeled_in_gmail = True
                record.save(update_fields=["labeled_in_gmail"])
            except Exception:
                logger.exception("Failed to apply Gmail label to message %s", gmail_id)
            scams_found += 1

        new_count += 1

    if new_count and not dry_run:
        generate_summary_reports()

    return {"scanned": len(gmail_ids), "new": new_count, "scams_found": scams_found}
