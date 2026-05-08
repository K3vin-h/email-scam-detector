"""
predict.py — Classify a single piece of text as scam or legitimate.

Run from the command line to test manually:
    python -m ml.predict "Congratulations! You've won a £1000 prize. Click here."
    python -m ml.predict "Hi Sarah, the meeting is moved to 3pm tomorrow."

This is also the function the Django app will call for each incoming email.
"""
import pickle
import sys
from pathlib import Path

import torch

from ml.model import ScamClassifier

ML_DIR = Path("ml")


def predict(text: str) -> tuple[bool, float]:
    """
    Classify one email text as scam or legitimate.

    Args:
        text: the raw email text (subject + body)

    Returns:
        is_scam    : True if the model thinks this is a scam
        confidence : float 0.0–1.0  (probability of being a scam)
                     e.g. 0.95 means "95% sure this is a scam"

    Note: this loads the model from disk on every call, which is fine for
    CLI testing. The Django app will load it once at startup instead.
    """
    # ── Load vectorizer ───────────────────────────────────────────────────────
    # The vectorizer knows the vocabulary learned during training.
    # We MUST use the same one — a different vocabulary would produce
    # meaningless numbers and garbage predictions.
    with open(ML_DIR / "vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    # ── Load model ────────────────────────────────────────────────────────────
    # Recreate the same architecture, then fill in the trained weights.
    input_dim = len(vectorizer.vocabulary_)
    model = ScamClassifier(input_dim)
    model.load_state_dict(torch.load(ML_DIR / "model.pt", map_location="cpu", weights_only=True))
    model.eval()  # Disable Dropout for deterministic output

    # ── Convert text → numbers → prediction ──────────────────────────────────
    # transform() (not fit_transform!) — we apply the existing vocabulary,
    # we do NOT learn new words from this single email.
    features = vectorizer.transform([text]).toarray()
    x = torch.tensor(features, dtype=torch.float32)

    with torch.no_grad():
        # .item() extracts the single Python float from the 1-element tensor.
        confidence = model(x).item()

    return confidence >= 0.5, confidence


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ml.predict \"email text here\"")
        sys.exit(1)

    text = " ".join(sys.argv[1:])
    is_scam, confidence = predict(text)

    label = "SCAM" if is_scam else "Legitimate"
    print(f"Result     : {label}")
    print(f"Confidence : {confidence:.1%} scam probability")
