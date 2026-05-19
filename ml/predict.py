"""
predict.py — Classify a single piece of text as scam or legitimate.

Run from the command line to test manually:
    python -m ml.predict "Congratulations! You've won a £1000 prize. Click here."
    python -m ml.predict "Hi Sarah, the meeting is moved to 3pm tomorrow."

This is also the function the Django app will call for each incoming email.
"""
import sys
from pathlib import Path

import torch

from ml.model import ScamClassifier
from ml.vectorizer_io import load_vectorizer

ML_DIR = Path("ml")


def load_predictor():
    """
    Load model artifacts once and return a callable for repeated predictions.

    This is useful for scan jobs that classify many emails in one run, avoiding
    repeated model and vectorizer deserialization for each message.
    """
    vectorizer = load_vectorizer(ML_DIR / "vectorizer.json")

    input_dim = len(vectorizer.vocabulary_)
    model = ScamClassifier(input_dim)
    try:
        state_dict = torch.load(ML_DIR / "model.pt", map_location="cpu", weights_only=True)
    except OSError as exc:
        raise RuntimeError("Model artifact not found: ml/model.pt") from exc
    model.load_state_dict(state_dict)
    model.eval()

    def _predict(text: str) -> tuple[bool, float]:
        features = vectorizer.transform([text]).toarray()
        x = torch.tensor(features, dtype=torch.float32)

        with torch.no_grad():
            confidence = model(x).item()

        return confidence >= 0.5, confidence

    return _predict


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
    return load_predictor()(text)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ml.predict \"email text here\"")
        sys.exit(1)

    text = " ".join(sys.argv[1:])
    is_scam, confidence = predict(text)

    label = "SCAM" if is_scam else "Legitimate"
    print(f"Result     : {label}")
    print(f"Confidence : {confidence:.1%} scam probability")
