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

from pathlib import Path
from typing import Any

from django.conf import settings
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


def get_credentials() -> Credentials | None:
    """
    Load saved credentials from token.json, refreshing if expired.
    Returns None if the user hasn't connected Gmail yet or if the token is invalid.
    """
    token_path = Path(settings.GMAIL_TOKEN_PATH)

    if not token_path.exists():
        return None

    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    except Exception:
        # token.json is corrupted or in an unreadable format — treat as not connected.
        return None

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
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


def _build_flow() -> Flow:
    """
    Create an OAuth flow using credentials from settings (pulled from .env).
    We pass the client ID/secret directly instead of using a credentials.json file.
    """
    client_config = {
        "web": {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GMAIL_REDIRECT_URI],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.GMAIL_REDIRECT_URI,
    )


def start_oauth(request: HttpRequest) -> HttpResponseRedirect:
    """Django view: send the user to Google's consent screen to approve access."""
    flow = _build_flow()
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
    return HttpResponseRedirect(auth_url)


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
    if state != request.session.get("oauth_state"):
        return HttpResponse("Invalid state parameter.", status=400)

    flow = _build_flow()
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return HttpResponse(f"Token exchange failed: {e}", status=400)

    token_path = Path(settings.GMAIL_TOKEN_PATH)
    try:
        token_path.write_text(flow.credentials.to_json())
    except OSError as e:
        return HttpResponse(f"Failed to save credentials: {e}", status=500)

    # TODO: once the React frontend exists, redirect to http://localhost:5173/settings?connected=true
    return HttpResponse("Gmail connected. You may close this tab.")
