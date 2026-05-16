# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the repo root. Activate the virtual environment first:

```bash
source venv/bin/activate
```

**ML pipeline (run in order for a fresh setup):**

```bash
python -m ml.download_data   # Download SpamAssassin + SMS Spam datasets → data/processed/emails.csv
python -m ml.train           # Fit TF-IDF, train network, save ml/model.pt + ml/vectorizer.pkl
python -m ml.evaluate        # Precision / recall / F1 on held-out test set (target: F1 ≥ 0.90)
python -m ml.predict "text"  # Quick manual inference check
```

**Lint:**

```bash
ruff check .
```

## Architecture

The project is a local macOS app that classifies Gmail emails as scam or legitimate using a PyTorch neural network trained from scratch. See `PLAN.md` for the full 10-phase roadmap.

**Current state:** Phases 1–4 complete (ML pipeline F1 = 0.97, Django scaffold + REST API). Phase 5+ (Gmail, React) not yet implemented.

### ML Pipeline (`ml/`)

Data flows in one direction through four scripts:

```
download_data.py  →  emails.csv  →  train.py  →  model.pt + vectorizer.pkl  →  predict.py
                                        ↓
                                    evaluate.py  (reads X_test.npy / y_test.npy saved by train.py)
```

- `download_data.py` — fetches SpamAssassin (`.tar.bz2`) and SMS Spam Collection (`.zip`), merges into `data/processed/emails.csv` with columns `text`, `label` (0 = legit, 1 = scam)
- `dataset.py` — `SpamDataset(Dataset)` wraps TF-IDF arrays as float32 tensors; labels get `unsqueeze(-1)` to match model output shape `(N, 1)`
- `model.py` — `ScamClassifier(nn.Module)`: Linear(input_dim→256) → ReLU → Dropout(0.3) → Linear(256→64) → ReLU → Dropout(0.3) → Linear(64→1) → Sigmoid
- `train.py` — fits `TfidfVectorizer(max_features=10_000)` on train split only, saves best checkpoint by val loss; hyperparameters (EPOCHS, BATCH_SIZE, LEARNING_RATE, MAX_FEATURES) are constants at the top of the file
- `predict.py` — `predict(text) → (is_scam: bool, confidence: float)`; loads model + vectorizer from disk on each CLI call (Django will load once at startup)

### Web Layer

- `core/` — Django project package (settings, urls, wsgi) ✓
- `dashboard/` — Django app (models: EmailRecord, ScanSettings, SummaryReport; DRF ViewSets) ✓
- `gmail/` — OAuth2 flow, email fetch, label application (Phase 5 — not yet implemented)
- `frontend/` — React 18 + Vite + Tailwind (port 5173); Django REST API on port 8000 (Phase 6 — not yet implemented)

### Key Constraints

- `ml/vectorizer.pkl` and `ml/model.pt` are gitignored — must run `ml.train` after cloning
- `data/processed/` is gitignored — must run `ml.download_data` first
- All `ml/` scripts use relative paths from the repo root (`Path("ml/")`, `Path("data/processed/")`); always run them as `python -m ml.<module>`, never as `python ml/train.py`
- Every `ml/` file has dense beginner-level comments explaining ML concepts — maintain this style when editing
