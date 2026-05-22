"""Email delivery for scam summary reports."""
import html
import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from dashboard.models import SummaryReport

logger = logging.getLogger(__name__)

_PERIOD_LABELS = {"daily": "Daily", "weekly": "Weekly", "monthly": "Monthly"}


def build_text_body(report: SummaryReport) -> str:
    """Plain-text email body — public for use in management command dry-run preview."""
    label = _PERIOD_LABELS.get(report.period, report.period)
    lines = [
        f"Scam Filter — {label} Summary",
        f"Generated: {report.generated_at:%Y-%m-%d %H:%M UTC}",
        "",
        f"Total scams detected: {report.total_scams}",
        "",
    ]
    if report.top_senders:
        lines.append("Top senders:")
        for i, entry in enumerate(report.top_senders, start=1):
            count = entry["count"]
            lines.append(f"  {i}. {entry['sender']} ({count} scam{'s' if count != 1 else ''})")
    else:
        lines.append("No scam senders to report.")
    lines += ["", f"View your full dashboard at {settings.FRONTEND_ORIGIN}"]
    return "\n".join(lines)


def build_html_body(report: SummaryReport) -> str:
    """HTML email body with styled layout. All user data is escaped."""
    label = _PERIOD_LABELS.get(report.period, report.period)
    generated = report.generated_at.strftime("%Y-%m-%d %H:%M UTC")

    # Each sender/count cell is escaped to prevent injection in the email client.
    sender_rows = "".join(
        f"<tr>"
        f"<td style='padding:7px 14px;border-bottom:1px solid #e5e7eb;'>"
        f"<code style='font-size:13px;color:#374151;'>{html.escape(entry['sender'])}</code></td>"
        f"<td style='padding:7px 14px;border-bottom:1px solid #e5e7eb;"
        f"text-align:center;font-weight:700;color:#ef4444;'>{int(entry['count'])}</td>"
        f"</tr>"
        for entry in report.top_senders
    )

    senders_section = (
        f"""
        <h3 style="font-size:14px;font-weight:700;color:#111827;margin:28px 0 10px;">
          Top Senders
        </h3>
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
          <thead><tr>
            <th style="text-align:left;padding:6px 14px;border-bottom:2px solid #e5e7eb;
                       color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">
              Sender
            </th>
            <th style="padding:6px 14px;border-bottom:2px solid #e5e7eb;
                       color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:.06em;">
              Scams
            </th>
          </tr></thead>
          <tbody>{sender_rows}</tbody>
        </table>"""
        if report.top_senders
        else "<p style='color:#6b7280;margin:20px 0 0;'>No scam senders to report.</p>"
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<body style="font-family:system-ui,-apple-system,sans-serif;background:#f3f4f6;
             padding:32px 16px;margin:0;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:14px;
              overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.10);">
    <div style="background:#7c3aed;padding:28px 32px;">
      <div style="font-size:11px;font-weight:700;letter-spacing:.1em;
                  text-transform:uppercase;color:#c4b5fd;margin-bottom:6px;">
        Scam Filter Report
      </div>
      <div style="font-size:28px;font-weight:800;color:#fff;">{label} Summary</div>
      <div style="font-size:12px;color:#ede9fe;margin-top:6px;">{generated}</div>
    </div>
    <div style="padding:28px 32px;">
      <div style="font-size:12px;font-weight:700;text-transform:uppercase;
                  letter-spacing:.07em;color:#6b7280;margin-bottom:8px;">
        Scams detected
      </div>
      <div style="font-size:52px;font-weight:800;color:#ef4444;line-height:1;">
        {report.total_scams}
      </div>
      {senders_section}
      <div style="margin-top:32px;padding-top:24px;border-top:1px solid #e5e7eb;">
        <a href="{html.escape(settings.FRONTEND_ORIGIN)}"
           style="display:inline-block;background:#7c3aed;color:#fff;font-weight:700;
                  font-size:13px;text-decoration:none;padding:11px 22px;border-radius:8px;">
          View Dashboard →
        </a>
      </div>
    </div>
  </div>
</body>
</html>"""


def send_summary_email(report: SummaryReport, recipient: str) -> bool:
    """Send a formatted scam summary email.

    Returns True on success; raises on SMTP error so the caller can decide
    whether to log, retry, or surface the failure.

    Args:
        report: The SummaryReport to include in the email.
        recipient: The destination email address (read from ScanSettings).
    """
    label = _PERIOD_LABELS.get(report.period, report.period)
    subject = f"Scam Filter — {label} Report"

    msg = EmailMultiAlternatives(
        subject=subject,
        body=build_text_body(report),
        from_email=settings.EMAIL_FROM,
        to=[recipient],
    )
    msg.attach_alternative(build_html_body(report), "text/html")
    msg.send()
    # Log domain only — avoid storing full email address as PII in logs
    domain = recipient.split("@")[-1] if "@" in recipient else "?"
    logger.info(
        "Summary email sent to ***@%s (period=%s, scams=%d)",
        domain,
        report.period,
        report.total_scams,
    )
    return True
