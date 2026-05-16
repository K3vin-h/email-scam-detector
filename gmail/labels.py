"""
Gmail label management.

Labels in Gmail are like folders — they tag emails so you can find them later.
We use two labels: "Scam" and "Legit", applied by the ML model's predictions.

The Gmail API requires a label ID (a string like "Label_123"), not the human
name, when applying labels to emails. get_or_create_label() handles the
name-to-ID lookup so callers can use plain English names.
"""

from gmail.auth import get_service


def get_or_create_label(name: str) -> str:
    """
    Return the Gmail label ID for `name`.
    Creates the label first if it doesn't already exist in the user's inbox.
    """
    service = get_service()

    existing = service.users().labels().list(userId="me").execute()
    for label in existing.get("labels", []):
        if label["name"] == name:
            return label["id"]

    # Label not found — create it and return the new ID.
    created = service.users().labels().create(
        userId="me", body={"name": name}
    ).execute()
    return created["id"]


def apply_label(email_id: str, label_id: str) -> None:
    """Apply label_id to the email identified by email_id."""
    service = get_service()
    service.users().messages().modify(
        userId="me",
        id=email_id,
        body={"addLabelIds": [label_id]},
    ).execute()
