# ML Model

## Feature extraction

Email text is vectorized with TF-IDF (`sklearn.feature_extraction.text.TfidfVectorizer`), capped at a 10,000-term vocabulary (`MAX_FEATURES`). The vectorizer is fit exclusively on the training split; validation and test splits are transformed with the fitted vocabulary only, to avoid vocabulary leakage inflating reported metrics. `sublinear_tf=True` applies log-scaling to raw term frequency so high-repetition terms don't dominate a document's vector disproportionately.

## Model architecture (`ml/model.py`)

A 3-layer fully-connected network:

```
input_dim (10,000) → Linear → 256 → ReLU → Dropout(0.3)
                    → Linear → 64  → ReLU → Dropout(0.3)
                    → Linear → 1   → Sigmoid
```

- Dropout(0.3) is active only during training (`model.train()`); disabled during inference (`model.eval()`) for deterministic output.
- Output is a single sigmoid-activated scalar in `[0, 1]`, interpreted as scam probability.

## Training pipeline (`ml/train.py`)

| Hyperparameter | Value |
|---|---|
| Epochs | 10 |
| Batch size | 64 |
| Learning rate | 1e-3 |
| Optimizer | Adam |
| Loss | Binary Cross-Entropy |
| Split | 70/15/15 (train/val/test), stratified, `random_state=42` |

Checkpointing saves `model.pt` only when validation loss improves epoch-over-epoch — the final artifact is the best-observed checkpoint, not the last epoch's weights. The test split is held out entirely until `ml/evaluate.py` runs once, post-training.

## Evaluation

Reported on the held-out test set: precision, recall, F1 (currently 0.9655). Precision/recall are tracked separately because the cost of a false positive (legitimate email suppressed) and a false negative (scam email missed) are not symmetric for this use case — see [Threshold design](#threshold-design).

## Threshold design

Two thresholds operate at different layers:

- `SCAM_THRESHOLD = 0.85` (`ml/predict.py`) — gates `is_scam` and the Gmail label application. Set high to bias toward precision over recall; a false "scam" label on a legitimate email is more disruptive to the user than a missed scam surfaced on the next scan.
- `POSSIBLE_SCAM_THRESHOLD = 0.50` (`dashboard/risk.py`) — gates the `possible_scam` UI tier for borderline confidence that doesn't meet the bar for an automatic label.

These are independent constants in separate modules; tuning one without the other is a known coupling risk (see [07-limitations.md](07-limitations.md)).

## Artifact serialization

Two artifacts are produced by training and consumed at inference: `ml/model.pt` (PyTorch state dict) and `ml/vectorizer.json` (TF-IDF vocabulary + IDF weights).

- `torch.load(..., weights_only=True)` restricts deserialization to tensor data, mitigating the arbitrary-code-execution risk of unrestricted pickle-based loading.
- The vectorizer is persisted as JSON rather than pickled (`ml/vectorizer_io.py`) for the same reason — it stores only vocabulary, IDF array, and vectorizer params, with an explicit `version` field checked on load. A previous version of this project used `vectorizer.pkl`; current prediction code assumes the JSON format only.

## Inference (`ml/predict.py`)

`load_predictor()` loads both artifacts once and returns a closure for repeated classification — used by the scan loop to avoid re-deserializing per email. `predict()` is a convenience wrapper that loads fresh on every call, used for CLI testing only.

## See also

- [03-scanning-and-risk.md](03-scanning-and-risk.md) — how model output combines with rule-based signals downstream
