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
from datetime import datetime, timezone as dt_timezone
from html.parser import HTMLParser
from typing import Any

from gmail.auth import get_service

# Hard cap to avoid exhausting Gmail API quota on large requests.
_MAX_RESULTS_LIMIT = 50


def list_emails(max_results: int | None = 10, query: str | None = None) -> list[dict]:
    """
    Return recent emails as a list of dicts.
    Each dict contains: id, subject, sender, snippet.
    `snippet` is a short preview of the email body provided by Gmail.
    `max_results` is capped at 50 unless set to None, which fetches all pages.
    `query` is passed through to Gmail search, such as after:YYYY/MM/DD.
    """
    service = get_service()
    emails = []
    page_token = None

    while True:
        page_size = _MAX_RESULTS_LIMIT if max_results is None else min(max_results, _MAX_RESULTS_LIMIT)
        result = service.users().messages().list(
            userId="me",
            maxResults=page_size,
            q=query,
            pageToken=page_token,
        ).execute()

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

        page_token = result.get("nextPageToken")
        if max_results is not None or not page_token:
            break

    return emails


def list_email_ids(max_results: int | None = 10, query: str | None = None) -> list[str]:
    """
    Return Gmail message IDs matching the query.

    This is the efficient scan path: callers that only need IDs can avoid the
    extra metadata request performed by list_emails().
    """
    service = get_service()
    email_ids = []
    page_token = None

    while True:
        remaining = None if max_results is None else max_results - len(email_ids)
        if remaining is not None and remaining <= 0:
            break

        page_size = _MAX_RESULTS_LIMIT if remaining is None else min(remaining, _MAX_RESULTS_LIMIT)
        result = service.users().messages().list(
            userId="me",
            maxResults=page_size,
            q=query,
            pageToken=page_token,
        ).execute()

        email_ids.extend(msg["id"] for msg in result.get("messages", []))

        page_token = result.get("nextPageToken")
        if not page_token:
            break

    return email_ids


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

    # internalDate is Unix time in milliseconds — convert to a timezone-aware datetime.
    internal_ms = int(detail.get("internalDate", 0))
    received_at = datetime.fromtimestamp(internal_ms / 1000, tz=dt_timezone.utc)

    return {
        "id": email_id,
        "subject": headers.get("Subject", "(no subject)"),
        "sender": headers.get("From", ""),
        "snippet": detail.get("snippet", ""),
        "body": _extract_body(detail.get("payload", {}), service, email_id),
        "received_at": received_at,
    }


class _HTMLTextExtractor(HTMLParser):
    """Collect readable text from HTML email bodies."""

    _IGNORED_TAGS = {"script", "style"}

    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._IGNORED_TAGS:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return

        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def _extract_body(payload: dict, service: Any, email_id: str) -> str:
    """
    Recursively walk a Gmail message payload tree to find readable email text.

    Gmail structures multi-part emails like a tree:
      multipart/mixed
        ├── multipart/alternative
        │     ├── text/plain   ← we want this
        │     └── text/html
        └── application/pdf   (attachment)

    We prefer text/plain, then fall back to text/html if no plain-text part exists.
    """
    plain_text = _extract_body_by_mime(payload, service, email_id, "text/plain")
    if plain_text:
        return plain_text

    html_text = _extract_body_by_mime(payload, service, email_id, "text/html")
    return _html_to_text(html_text) if html_text else ""


def _extract_body_by_mime(
    payload: dict,
    service: Any,
    email_id: str,
    mime_type: str,
) -> str:
    """Find and decode the first body part matching the requested MIME type."""
    if payload.get("mimeType") == mime_type and not _is_attachment(payload):
        return _decode_part_body(payload, service, email_id)

    for part in payload.get("parts", []):
        result = _extract_body_by_mime(part, service, email_id, mime_type)
        if result:
            return result

    return ""


def _is_attachment(payload: dict) -> bool:
    """Return True when this payload part is an attachment, not message body text."""
    if payload.get("filename"):
        return True

    headers = {
        header.get("name", "").lower(): header.get("value", "").lower()
        for header in payload.get("headers", [])
    }
    return "attachment" in headers.get("content-disposition", "")


def _decode_part_body(payload: dict, service: Any, email_id: str) -> str:
    """Decode an inline Gmail body part or fetch it by attachment ID first."""
    body = payload.get("body", {})
    data = body.get("data", "")

    if not data and body.get("attachmentId"):
        attachment = service.users().messages().attachments().get(
            userId="me",
            messageId=email_id,
            id=body["attachmentId"],
        ).execute()
        data = attachment.get("data", "")

    if not data:
        return ""

    # Gmail uses URL-safe base64. Padding to a multiple of 4 ensures valid decoding.
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="replace")


def _html_to_text(html: str) -> str:
    """Convert a simple HTML email body into plain text for classification."""
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()
