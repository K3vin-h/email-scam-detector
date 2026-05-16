"""
Gmail email fetching.

The Gmail API returns emails in a two-step process:
  1. messages.list()  →  gives us a list of message IDs (no content yet)
  2. messages.get()   →  fetches the full email for each ID

Email bodies are base64-encoded by Gmail (a way of encoding binary data
as text). We decode them back to a readable string before returning.

Multi-part emails (text + HTML + attachments) are structured as a tree.
We walk the tree recursively to find the plain-text part.
"""

import base64

from gmail.auth import get_service

# Hard cap to avoid exhausting Gmail API quota on large requests.
_MAX_RESULTS_LIMIT = 50


def list_emails(max_results: int = 10) -> list[dict]:
    """
    Return recent emails as a list of dicts.
    Each dict contains: id, subject, sender, snippet.
    `snippet` is a short preview of the email body provided by Gmail.
    `max_results` is capped at 50 to stay within API quota limits.
    """
    service = get_service()
    max_results = min(max_results, _MAX_RESULTS_LIMIT)

    result = service.users().messages().list(
        userId="me", maxResults=max_results
    ).execute()

    emails = []
    for msg in result.get("messages", []):
        # format="metadata" fetches only headers (Subject, From), not the full body.
        # This is faster than fetching the full email for a list view.
        detail = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From"],
        ).execute()

        headers = {
            h["name"]: h["value"]
            for h in detail.get("payload", {}).get("headers", [])
        }
        emails.append({
            "id": msg["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "sender": headers.get("From", ""),
            "snippet": detail.get("snippet", ""),
        })

    return emails


def get_email(email_id: str) -> dict:
    """
    Return a single email as a dict.
    Includes id, subject, sender, snippet, and decoded plain-text body.
    """
    service = get_service()

    # format="full" fetches the entire email including the body payload.
    detail = service.users().messages().get(
        userId="me", id=email_id, format="full"
    ).execute()

    headers = {
        h["name"]: h["value"]
        for h in detail.get("payload", {}).get("headers", [])
    }

    return {
        "id": email_id,
        "subject": headers.get("Subject", "(no subject)"),
        "sender": headers.get("From", ""),
        "snippet": detail.get("snippet", ""),
        "body": _extract_body(detail.get("payload", {})),
    }


def _extract_body(payload: dict) -> str:
    """
    Recursively walk a Gmail message payload tree to find the plain-text body.

    Gmail structures multi-part emails like a tree:
      multipart/mixed
        ├── multipart/alternative
        │     ├── text/plain   ← we want this
        │     └── text/html
        └── application/pdf   (attachment)

    We stop at the first text/plain node we find.
    Returns an empty string if no plain-text part exists.
    """
    if payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        # Gmail uses URL-safe base64. Padding to a multiple of 4 ensures valid decoding.
        padding = "=" * (4 - len(data) % 4) if data else ""
        return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_body(part)
        if result:
            return result

    return ""
