"""
evaluate.py — Tests the trained model on held-out data it has never seen.

Run: python -m ml.evaluate

This gives an honest measure of real-world performance.
The test set was saved by train.py and was never used during training.

Metrics explained:
  Precision : of emails we flagged as scam, what % actually were scam?
              (low precision = many false alarms)
  Recall    : of all actual scam emails, what % did we catch?
              (low recall = missing real scams)
  F1 Score  : harmonic mean of precision and recall — our main target (≥ 0.90)
  Accuracy  : % of all emails correctly classified
"""
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import classification_report, f1_score

from ml.model import ScamClassifier

ML_DIR = Path("ml")
PROCESSED_DIR = Path("data/processed")


def main():
    # ── Load test set saved by train.py ───────────────────────────────────────
    X_test = np.load(PROCESSED_DIR / "X_test.npy")
    y_test = np.load(PROCESSED_DIR / "y_test.npy")

    # ── Rebuild the model and load trained weights ────────────────────────────
    # We recreate the same architecture used in train.py.
    # Then load_state_dict() fills in the saved weights.
    # map_location="cpu" ensures it loads correctly even if originally trained on GPU.
    model = ScamClassifier(input_dim=X_test.shape[1])
    model.load_state_dict(torch.load(ML_DIR / "model.pt", map_location="cpu", weights_only=True))

    # eval() disables Dropout for consistent, deterministic predictions.
    model.eval()

    # ── Run inference ─────────────────────────────────────────────────────────
    X_tensor = torch.tensor(X_test, dtype=torch.float32)
    with torch.no_grad():
        # The model outputs probabilities. squeeze() removes the extra dimension
        # so shape goes from (N, 1) to (N,).
        probs = model(X_tensor).squeeze().numpy()

    # Threshold at 0.5: probability >= 0.5 → predicted scam (1), else legit (0).
    y_pred = (probs >= 0.5).astype(int)

    # ── Print results ─────────────────────────────────────────────────────────
    print("Test Set Results")
    print("=" * 50)
    print(classification_report(y_test, y_pred, target_names=["Legit", "Scam"]))

    f1 = f1_score(y_test, y_pred)
    print(f"F1 Score: {f1:.4f}")
    if f1 >= 0.90:
        print("Target met (F1 >= 0.90) — ready for integration.")
    else:
        print("Below target. Try: more epochs, more data, or adjust MAX_FEATURES in train.py.")


if __name__ == "__main__":
    main()
