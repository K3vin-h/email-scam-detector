# Scanning and Risk Classification

## Two independent signal sources

The system produces two distinct kinds of output per email, computed independently:

1. **Model confidence** (`ml/predict.py`) — a single float from the neural network.
2. **Reason tags** (`dashboard/scanner.py::_extract_reasons`) — rule-based keyword matches (urgency language, credential requests, cash-incentive language, lookalike domains, suspicious TLDs, crypto/investment language), returned only when an email is already classified as scam. These are not model outputs and do not influence `confidence`.

The two are combined for display but never fused into a single score — the reason tags are explanatory metadata on top of the classifier's decision, not an input to it.

## Risk resolution (`dashboard/risk.py`)

```python
def risk_level_for_email(*, sender, confidence, is_scam, user_risk_override=""):
    if user_risk_override in RISK_LEVELS:
        return user_risk_override
    if is_trusted_legit_sender(sender):
        return RISK_LEGIT
    if is_scam and confidence >= SCAM_THRESHOLD:      # 0.85
        return RISK_SCAM
    if is_scam or confidence >= POSSIBLE_SCAM_THRESHOLD:  # 0.50
        return RISK_POSSIBLE
    return RISK_LEGIT
```

Precedence, in order: manual override → trusted-domain allowlist → high-confidence threshold → mid-confidence threshold → default legit. `TRUSTED_LEGIT_DOMAINS` is a hardcoded allowlist for specific domains observed to be over-flagged by the model; it is a point patch, not a general solution (see [07-limitations.md](07-limitations.md)).

Note that `EmailRecord.is_scam` stores the **risk-adjusted** result, not the model's raw threshold check — an email the model scored above 0.85 but whose sender matches the trusted allowlist is persisted with `is_scam=False`.

## Scan orchestration (`dashboard/scanner.py::run_scan`)

1. Load `ScanSettings.scan_window_days`; build a Gmail search query (`after:YYYY/MM/DD`).
2. List candidate message IDs; diff against existing `gmail_id`s (bulk lookup) to skip already-scanned messages.
3. For unseen messages: fetch full body, classify, resolve risk level, extract reason tags if scam, persist `EmailRecord`.
4. Apply the Gmail `Scam` label lazily — the label ID is resolved once per scan run and cached locally to avoid a redundant API call per flagged message.
5. For already-scanned messages whose current risk level is `scam` but not yet labeled (e.g. due to a subsequent manual correction), retroactively apply the label.
6. On any new record, regenerate summary reports.

`dry_run=True` executes classification without persistence or Gmail mutation — used by the CLI and for report-generation dry-runs.

## Duplicate-scan safety

`gmail_id` uniqueness plus a bulk `in_bulk()` lookup before processing makes `run_scan()` safe to call concurrently or repeatedly without producing duplicate rows; `get_or_create` on insert is the final safeguard against a race between the existence check and the write.

## See also

- [01-ml-model.md](01-ml-model.md) — model internals
- [02-django-backend.md](02-django-backend.md) — `EmailRecord` schema
- [07-limitations.md](07-limitations.md) — allowlist and threshold coupling
