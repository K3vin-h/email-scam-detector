from email.utils import parseaddr

from ml.predict import SCAM_THRESHOLD

POSSIBLE_SCAM_THRESHOLD = 0.50
RISK_LEGIT = "legit"
RISK_POSSIBLE = "possible_scam"
RISK_SCAM = "scam"
RISK_LEVELS = {RISK_LEGIT, RISK_POSSIBLE, RISK_SCAM}

TRUSTED_LEGIT_DOMAINS = {
    "adobe.com",
    "ppy.sh",
}


def sender_domain(sender: str) -> str:
    """Extract a lowercase sender domain from a raw email sender string."""
    _, address = parseaddr(sender)
    value = address or sender
    return value.rsplit("@", 1)[-1].strip().lower()


def is_trusted_legit_sender(sender: str) -> bool:
    """Return True for known legitimate sender domains the model over-flags."""
    domain = sender_domain(sender)
    return any(domain == trusted or domain.endswith(f".{trusted}") for trusted in TRUSTED_LEGIT_DOMAINS)


def risk_level_for_email(*, sender: str, confidence: float, is_scam: bool, user_risk_override: str = "") -> str:
    """Return the app-level risk tag for an email."""
    if user_risk_override in RISK_LEVELS:
        return user_risk_override
    if is_trusted_legit_sender(sender):
        return RISK_LEGIT
    if is_scam and confidence >= SCAM_THRESHOLD:
        return RISK_SCAM
    if is_scam or confidence >= POSSIBLE_SCAM_THRESHOLD:
        return RISK_POSSIBLE
    return RISK_LEGIT


def risk_label(risk_level: str) -> str:
    labels = {
        RISK_LEGIT: "Legit",
        RISK_POSSIBLE: "Possible scam",
        RISK_SCAM: "Scam",
    }
    return labels.get(risk_level, "Legit")
