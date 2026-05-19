"""
Gmail OAuth 2.0 authentication.

OAuth is a protocol that lets users grant this app access to their Gmail
without sharing their password. Here's how the flow works:

  1. User visits /auth/gmail/  →  we redirect them to Google's consent screen
  2. User approves access      →  Google redirects back to /auth/callback/?code=...
  3. We exchange that code     →  Google returns an access token + refresh token
  4. We save the tokens to token.json so future requests don't need re-auth

Access tokens expire after ~1 hour. The refresh token lets us get a new
access token automatically without making the user log in again.
"""

import logging
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# Scopes define exactly what permissions we're requesting from the user.
# readonly = read emails, labels = see label names, modify = apply labels.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.labels",
    "https://www.googleapis.com/auth/gmail.modify",
]

logger = logging.getLogger(__name__)
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/" + "token"


def get_credentials() -> Credentials | None:
    """
    Load saved credentials from token.json, refreshing if expired.
    Returns None if the user hasn't connected Gmail yet or if the token is invalid.
    """
    token_path = Path(settings.GMAIL_TOKEN_PATH)

    if not token_path.exists():
        return None

    try:
        os.chmod(token_path, 0o600)
    except OSError:
        logger.exception("Failed to secure Gmail OAuth token file")
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except Exception:
        # token.json is corrupted or in an unreadable format — treat as not connected.
        return None

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _write_token_file(token_path, creds.to_json())
        except Exception:
            # Refresh failed — token may have been revoked by the user.
            return None

    return creds if creds.valid else None


def get_service() -> Any:
    """
    Build and return an authenticated Gmail API client.
    Raises RuntimeError if the user hasn't completed OAuth yet.
    """
    creds = get_credentials()
    if not creds:
        raise RuntimeError("No valid Gmail credentials. Visit /auth/gmail/ to connect.")
    return build("gmail", "v1", credentials=creds)


def _build_flow(state: str | None = None, code_verifier: str | None = None) -> Flow:
    """
    Create an OAuth flow using credentials from settings (pulled from .env).
    We pass the client ID/secret directly instead of using a credentials.json file.
    """
    if not settings.GMAIL_CLIENT_ID or not settings.GMAIL_CLIENT_SECRET:
        raise RuntimeError(
            "Gmail OAuth is not configured. Set GMAIL_CLIENT_ID and "
            "GMAIL_CLIENT_SECRET in .env."
        )

    client_config = {
        "web": {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": _GOOGLE_TOKEN_URI,
            "redirect_uris": [settings.GMAIL_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.GMAIL_REDIRECT_URI,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=True,
    )


def _write_token_file(token_path: Path, token_json: str) -> None:
    """Write OAuth tokens so only the local OS user can read them."""
    fd = os.open(token_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as token_file:
        token_file.write(token_json)
    os.chmod(token_path, 0o600)


@login_required
def start_oauth(request: HttpRequest) -> HttpResponse | HttpResponseRedirect:
    """Django view: send the user to Google's consent screen to approve access."""
    try:
        flow = _build_flow()
    except RuntimeError as e:
        return HttpResponse(str(e), status=500)

    # access_type="offline" ensures Google gives us a refresh token.
    # prompt="consent" forces the consent screen even if the user approved before.
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    # Store state in the session so oauth_callback can verify it.
    # This prevents CSRF attacks where an attacker tricks the server into
    # accepting a malicious auth code by forging the callback URL.
    request.session["oauth_state"] = state
    request.session["oauth_code_verifier"] = flow.code_verifier
    return HttpResponseRedirect(auth_url)


@login_required
def oauth_callback(request: HttpRequest) -> HttpResponse:
    """
    Django view: Google redirects here after the user approves access.
    We verify the state, exchange the one-time auth code for tokens, and save them.
    """
    code = request.GET.get("code")
    state = request.GET.get("state")

    if not code:
        return HttpResponse("Missing authorization code.", status=400)

    # Verify state matches what we stored in the session — rejects forged callbacks.
    saved_state = request.session.get("oauth_state")
    code_verifier = request.session.get("oauth_code_verifier")

    if not saved_state or not state or state != saved_state:
        return HttpResponse("Invalid state parameter.", status=400)

    if not code_verifier:
        return HttpResponse("Missing OAuth verifier.", status=400)

    flow = _build_flow(state=saved_state, code_verifier=code_verifier)
    try:
        flow.fetch_token(code=code)
    except Exception:
        logger.exception("Gmail OAuth token exchange failed")
        return HttpResponse("Failed to connect Gmail. Please try again.", status=400)

    request.session.pop("oauth_state", None)
    request.session.pop("oauth_code_verifier", None)

    token_path = Path(settings.GMAIL_TOKEN_PATH)
    try:
        _write_token_file(token_path, flow.credentials.to_json())
    except OSError:
        logger.exception("Failed to save Gmail OAuth credentials")
        return HttpResponse("Failed to save Gmail credentials.", status=500)

    # TODO: once the React frontend exists, redirect to http://localhost:5173/settings?connected=true
    return HttpResponse("Gmail connected. You may close this tab.")
