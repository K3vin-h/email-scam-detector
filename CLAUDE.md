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
python -m ml.train           # Fit TF-IDF, train network, save ml/model.pt + ml/vectorizer.json
python -m ml.evaluate        # Precision / recall / F1 on held-out test set (target: F1 ≥ 0.90)
python -m ml.predict "text"  # Quick manual inference check
```

**Backend:**

```bash
python manage.py migrate
python manage.py createsuperuser  # first local setup only
python manage.py runserver        # Django API/admin on http://localhost:8000
python manage.py scan_emails      # Run Gmail scan and persist/label results
python manage.py scan_emails --dry-run  # Classify without DB writes or Gmail labels
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev -- --port 5173  # React UI on http://localhost:5173
```

If Vite uses another port, add that origin to `CORS_ALLOWED_ORIGINS`,
`CSRF_TRUSTED_ORIGINS`, and `FRONTEND_ORIGIN` in `.env`, then restart Django.

**Checks:**

```bash
ruff check .
python manage.py test
python -m bandit -r core dashboard gmail ml -q
python -m pip_audit -r requirements.txt
cd frontend && npm test -- --run
cd frontend && npm audit
```

## Architecture

The project is a local macOS app that classifies Gmail emails as scam or legitimate using a PyTorch neural network trained from scratch. See `PLAN.md` for the full 10-phase roadmap.

**Current state:** Phases 1–8 complete. The ML pipeline, Django backend, Gmail OAuth/fetch/labels integration, dashboard models, REST API, scan command, and React/Vite frontend are implemented. Security hardening is also in place: authenticated API defaults, DRF throttling, CSRF/CORS configuration, production security settings, safe scan error responses, and JSON-based vectorizer artifacts instead of pickle loading. Phases 9–10 (background scheduling and generated summary/report automation) remain future work.

### ML Pipeline (`ml/`)

Data flows in one direction through four scripts:

```
download_data.py  →  emails.csv  →  train.py  →  model.pt + vectorizer.json  →  predict.py
                                        ↓
                                    evaluate.py  (reads X_test.npy / y_test.npy saved by train.py)
```

- `download_data.py` — fetches SpamAssassin (`.tar.bz2`) and SMS Spam Collection (`.zip`), merges into `data/processed/emails.csv` with columns `text`, `label` (0 = legit, 1 = scam)
- `dataset.py` — `SpamDataset(Dataset)` wraps TF-IDF arrays as float32 tensors; labels get `unsqueeze(-1)` to match model output shape `(N, 1)`
- `model.py` — `ScamClassifier(nn.Module)`: Linear(input_dim→256) → ReLU → Dropout(0.3) → Linear(256→64) → ReLU → Dropout(0.3) → Linear(64→1) → Sigmoid
- `train.py` — fits `TfidfVectorizer(max_features=10_000)` on train split only, saves best checkpoint by val loss, and writes the vectorizer as JSON; hyperparameters (EPOCHS, BATCH_SIZE, LEARNING_RATE, MAX_FEATURES) are constants at the top of the file
- `vectorizer_io.py` — saves/loads the fitted TF-IDF vectorizer as trusted JSON to avoid unsafe pickle deserialization
- `predict.py` — `predict(text) → (is_scam: bool, confidence: float)`; loads model + vectorizer from disk on each CLI call, while scan jobs load the predictor once and reuse it

### Web Layer

- `core/` — Django project package (settings, urls, wsgi). DRF defaults require authentication, throttle requests, and render JSON only. Production security settings default to strict values when `DEBUG=False`.
- `dashboard/` — Django app with `EmailRecord`, `ScanSettings`, and `SummaryReport`; authenticated DRF endpoints for emails, stats, settings, reports, and scan triggering; `scan_emails` management command.
- `dashboard/scanner.py` — lists Gmail IDs with the scan-window query, bulk-skips already-known records, fetches/classifies only new messages, retries labels for known unlabeled scams, honors `dry_run`, and uses atomic `get_or_create` for scan inserts.
- `gmail/` — OAuth2 flow with session state + PKCE verifier protection (`auth.py`); email fetch with plain-text + HTML fallback and attachment handling (`fetch.py`); efficient ID-only listing for scans; label create/apply (`labels.py`); token saved to `token.json` (gitignored).
- `frontend/` — React + Vite + Tailwind UI on port 5173. Structure:
  - `pages/` — `LoginPage`, `DashboardPage`, `ReportsPage`, `SettingsPage`
  - `components/` — `NavBar`, `EmailRow`, `FilterBar`, `Pagination`, `ScanButton`, `StatCard`, `ReportCard`
  - `hooks/` — `useAuth`, `useEmails`, `useStats`, `useReports`, `useSettings` (data-fetching hooks)
  - `api/client.js` — centralized fetch wrapper; sends `credentials: "include"` and `X-CSRFToken` header on mutating requests
  - `__tests__/` — Vitest unit tests for API client, hooks, and page components

### Key Constraints

- `ml/vectorizer.json`, legacy `ml/vectorizer.pkl`, and `ml/model.pt` are gitignored — must run `ml.train` after cloning or artifact cleanup
- `data/processed/` is gitignored — must run `ml.download_data` first
- `frontend/node_modules/` must not be committed; commit `frontend/package.json` and `frontend/package-lock.json`, then run `npm install`
- `AGENTS.md`, `.env`, `token.json`, `credentials.json`, and `db.sqlite3` are gitignored and must stay local
- Keep frontend dev origin and backend trusted origins aligned. Default expected frontend origin is `http://localhost:5173`; if Vite starts on `5176`, update `.env` (`CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `FRONTEND_ORIGIN`) and restart Django.
- All `ml/` scripts use relative paths from the repo root (`Path("ml/")`, `Path("data/processed/")`); always run them as `python -m ml.<module>`, never as `python ml/train.py`
- Every `ml/` file has dense beginner-level comments explaining ML concepts — maintain this style when editing
