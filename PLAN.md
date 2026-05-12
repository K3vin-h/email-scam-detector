# Scam Email Filter — Implementation Plan

> This file will be copied to `/Users/shibah/Documents/VS Code/scam filter/PLAN.md` at the start of implementation.

## Context

Build a local Django web app that uses a PyTorch neural network (trained from scratch) to detect scam emails in Gmail. The user is new to PyTorch/ML but knows Python. The app labels scams in Gmail, shows a dashboard, and generates configurable summary reports. Everything runs locally on macOS.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Web framework | Django 5.x |
| ML | PyTorch 2.x |
| Text features | scikit-learn TF-IDF vectorizer |
| Gmail API | google-auth-oauthlib + google-api-python-client |
| Background scheduler | APScheduler (integrated into Django) |
| Database | SQLite (local, zero config) |
| Frontend | React (Vite) + Tailwind CSS — Django serves REST API, React is the UI |

## Code Quality Rules (enforced after every session)

- No file over 800 lines. Split if needed.
- No function over 50 lines. Extract if needed.
- No file created unless it is referenced and used by existing code.
- No function created unless it is called from at least one place.
- No abstraction added speculatively — only extract when duplication is real (3+ identical usages).
- After every coding session: scan all modified files for dead code, unused imports, and redundant functions. Remove them before stopping.
- Modern Python (3.11+): use `pathlib` over `os.path`, f-strings over `.format()`, `|` union types, dataclasses where appropriate.
- Modern PyTorch: use `torch.compile()` where applicable, `DataLoader` with `pin_memory=True` and `num_workers` for performance.

## Agent Model Policy

| Task | Model |
|---|---|
| Research (datasets, APIs, libraries) | Haiku |
| Code writing & debugging | Sonnet |

---

## ML Code Style — Beginner Comments (Zero ML Background)

Every `ml/` file must have comments that explain **what the concept is**, not just what the line does. Assume the reader knows basic Python but has never touched machine learning.

### Key concepts to explain inline wherever they appear

| Concept | Plain-English explanation to include in comments |
|---|---|
| Tensor | A PyTorch "tensor" is just a list of numbers (or a grid of numbers). It's like a Python list, but PyTorch can do math on it very fast using your GPU/CPU. |
| Neural network | A stack of math functions chained together. Each "layer" takes numbers in, multiplies them by learned weights, and passes new numbers to the next layer. |
| `nn.Linear(a, b)` | A layer that takes `a` numbers and outputs `b` numbers. Internally it holds a grid of weights (a×b numbers) that get adjusted during training. |
| ReLU | An activation function. It just does `max(0, x)` — turns negative numbers to 0. This lets the network learn non-linear patterns. |
| Dropout | During training, randomly zeroes out some neurons. Sounds weird, but it forces the network not to rely on any one neuron and prevents "memorising" the training data (overfitting). |
| Sigmoid | Squishes any number into the range 0–1. Used at the end so the output is a probability ("how confident am I this is a scam?"). |
| Loss / loss function | A number that measures how wrong the model's predictions are. During training, we try to make this number as small as possible. |
| Backpropagation | How the model learns. After each batch, PyTorch automatically figures out which weights caused the error and nudges them in the right direction. |
| Optimizer | The algorithm that does the actual weight nudging. We use Adam, which is a popular default that works well. |
| Epoch | One full pass through the entire training dataset. We repeat this many times (e.g. 10 epochs) until the model stops improving. |
| TF-IDF | A way to turn an email (text) into numbers. It counts how often each word appears and down-weights words that appear in every email (like "the"). The result is a list of numbers PyTorch can process. |
| Training / validation / test split | We split data into 3 groups: train (the model learns from this), validation (we tune on this), test (one final check the model has never seen). This prevents cheating. |

### Example of expected comment density

```python
# ── What is a "Dataset"? ────────────────────────────────────────────────────
# PyTorch needs data in a specific format called a Dataset.
# A Dataset is just a Python class with two methods:
#   __len__  → tells PyTorch how many emails we have
#   __getitem__ → gives PyTorch one email (as numbers) + its label (0=legit, 1=scam)
# PyTorch will call these automatically during training.
class SpamDataset(torch.utils.data.Dataset):

    def __init__(self, features, labels):
        # Convert our numpy arrays (from TF-IDF) into PyTorch tensors.
        # float32 is the number format neural nets expect.
        self.X = torch.tensor(features, dtype=torch.float32)
        # Labels are 0 or 1. unsqueeze(-1) reshapes from [N] to [N, 1]
        # because our model outputs a single number per email.
        self.y = torch.tensor(labels, dtype=torch.float32).unsqueeze(-1)

    def __len__(self):
        # PyTorch calls this to know the total dataset size.
        return len(self.y)

    def __getitem__(self, idx):
        # PyTorch calls this with an index to get one sample.
        # Returns (features_for_one_email, label_for_one_email).
        return self.X[idx], self.y[idx]
```

---

## Project Structure

```
scam-filter/
├── manage.py
├── requirements.txt
├── .env.example
├── data/
│   ├── raw/               # Downloaded SpamAssassin / Enron datasets
│   └── processed/         # Tokenized & vectorized splits
├── ml/
│   ├── __init__.py
│   ├── dataset.py         # PyTorch Dataset class
│   ├── model.py           # Feedforward net definition
│   ├── train.py           # Training loop with loss/accuracy logging
│   ├── evaluate.py        # Precision, recall, F1 on test set
│   ├── predict.py         # Single-email inference function
│   └── vectorizer.pkl     # Saved TF-IDF vectorizer (gitignored)
├── gmail/
│   ├── __init__.py
│   ├── auth.py            # OAuth2 flow, token refresh
│   ├── fetch.py           # List + fetch email messages
│   └── labels.py          # Create/apply "Scam" label
├── core/                  # Django project package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── dashboard/             # Django app
    ├── models.py          # EmailRecord, ScanSettings, SummaryReport
    ├── views.py
    ├── urls.py
    └── management/
        └── commands/
            ├── download_data.py  # Fetch public datasets
            ├── train_model.py    # Run ML training pipeline
            └── scan_emails.py    # On-demand Gmail scan
frontend/                  # React app (Vite + Tailwind)
├── src/
│   ├── App.jsx
│   ├── pages/
│   │   ├── Dashboard.jsx      # Scam list + stats
│   │   ├── Reports.jsx        # Summary reports
│   │   └── Settings.jsx       # Scan + notification config
│   ├── components/
│   │   ├── EmailCard.jsx
│   │   ├── StatsBar.jsx
│   │   └── ScanButton.jsx
│   └── api/
│       └── client.js          # fetch() calls to Django REST API
├── package.json
└── vite.config.js
```

---

## Implementation Phases

> **Phases 1–3 are fully standalone Python — no Django, no React, no Gmail.**
> Complete and verify each phase before moving on.

> **After completing each phase:** write a detailed phase report directly below that phase's section. The report is written for a complete beginner who knows basic Python but nothing about software engineering or ML. It must include:
> - **What was built** — every file created or modified, what it does, and why it exists
> - **How the files connect** — explain the data/call flow between files in plain English
> - **Key concepts explained** — define every non-obvious concept introduced (e.g. what is a vectorizer? what is a Django app? what is a REST API?)
> - **Why each design decision was made** — don't just say what the code does, explain *why* it was written that way
> - **Current state of the project** — what can run right now, what can't, what comes next
> - **Any deviations from the original plan** — what changed and why
>
> Update `CLAUDE.md` if any architectural facts changed.

### Phase 1 — Data Download (`ml/download_data.py`)

Standalone script (no Django needed yet):
- Downloads SpamAssassin public corpus (ham + spam `.txt` files)
- Downloads Enron spam dataset (CSV)
- Merges into a single `data/processed/emails.csv` with columns: `text`, `label` (0=legit, 1=scam)
- Prints row count and class balance so we know the data looks right
- Run with: `python -m ml.download_data`

### Phase 2 — ML Pipeline (`ml/`)

All files are plain Python modules — runnable without Django.

**Dataset** (`ml/dataset.py`):
- `SpamDataset(torch.utils.data.Dataset)` — loads `emails.csv`, returns `(features_tensor, label_tensor)`
- Detailed beginner comments explaining every line (see ML Code Style section above)

**Model** (`ml/model.py`):
- `ScamClassifier(nn.Module)` — feedforward net:
  - `Linear(input_dim, 256)` → ReLU → Dropout(0.3)
  - `Linear(256, 64)` → ReLU → Dropout(0.3)
  - `Linear(64, 1)` → Sigmoid
- Binary cross-entropy loss
- Detailed beginner comments on every concept

**Training** (`ml/train.py`):
- TF-IDF vectorizer fit on train split, saved to `ml/vectorizer.pkl`
- Train/val/test split: 70% / 15% / 15%
- Training loop prints per-epoch loss + accuracy for both train and val sets
- Saves best checkpoint to `ml/model.pt` (only when val loss improves)
- Run with: `python -m ml.train`

**Evaluation** (`ml/evaluate.py`):
- Loads saved `model.pt` + `vectorizer.pkl`
- Runs on held-out test set, prints precision / recall / F1 / accuracy
- Run with: `python -m ml.evaluate`

**Inference** (`ml/predict.py`):
- `predict(text: str) -> tuple[bool, float]` — loads model + vectorizer, returns `(is_scam, confidence)`
- Also has a `__main__` block: `python -m ml.predict "Congratulations, you've won..."` for quick manual testing

### Phase 3 — Standalone Verification (gate before web layer)

Before writing any Django code, confirm:
- [ ] `python -m ml.download_data` completes, `data/processed/emails.csv` exists
- [ ] `python -m ml.train` runs 10 epochs, loss goes down each epoch
- [ ] `python -m ml.evaluate` reports F1 ≥ 0.90
- [ ] `python -m ml.predict "You have won a prize click here"` returns `(True, >0.8)`
- [ ] `python -m ml.predict "Hi, your meeting is at 3pm"` returns `(False, <0.2)`

**Only proceed to Phase 4 after all 5 checks pass.**

---

### Phase 4 — Django Scaffold + REST API

- `django-admin startproject core .`
- `python manage.py startapp dashboard`
- `requirements.txt` updated with Django + DRF + CORS deps
- `.env.example` with `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `SECRET_KEY`
- SQLite configured in `core/settings.py`

### Phase 5 — Gmail Integration (`gmail/`)

- `auth.py`: OAuth2 consent flow on first run, stores `token.json` locally
- `fetch.py`: `list_emails(max_results, since_date)` — returns list of `{id, subject, body, sender, date}`
- `labels.py`: `ensure_scam_label()`, `apply_scam_label(message_id)`

### Phase 6 — Django Models (`dashboard/models.py`)

```python
class EmailRecord:       # id, gmail_id, sender, subject, snippet, received_at, confidence, is_scam, labeled_in_gmail
class ScanSettings:      # singleton — scan_window_days, scan_frequency_hours, notify_frequency (daily/weekly/monthly), notify_via_email, notify_email_address
class SummaryReport:     # period (daily/weekly/monthly), generated_at, total_scams, top_senders JSON
```

### Phase 7 — Django REST API (`dashboard/`)

Django serves JSON endpoints consumed by the React frontend:

- `GET /api/emails/` — paginated scam list with confidence scores
- `GET /api/reports/?period=daily|weekly|monthly` — summary reports
- `GET/PATCH /api/settings/` — read/update ScanSettings
- `POST /api/scan/` — trigger on-demand scan
- `GET /api/stats/` — aggregate counts for dashboard charts

Uses Django REST Framework (DRF) with serializers.

### Phase 8 — React Frontend (`frontend/`)

- Vite + React 18 + JavaScript + Tailwind CSS
- `api/client.js` wraps all fetch calls to `http://localhost:8000/api/`
- Pages: Dashboard (scam list + stats), Reports (period filter), Settings
- `npm run dev` runs on port 5173; Django runs on 8000 (CORS configured)

### Phase 9 — Background Scheduler

- APScheduler `BackgroundScheduler` started in `dashboard/apps.py` `ready()` hook
- Reads `ScanSettings.scan_frequency_hours` to set interval
- Calls same logic as `scan_emails` management command
- On-demand scan also available via dashboard "Scan Now" button

### Phase 10 — Summary Reports

- Django management command or scheduled job generates `SummaryReport` records
- Dashboard `/reports/` renders them with period filter
- Optional: email summary to `notify_email_address` via `smtplib` (configurable in Settings)

---

## Key Files to Create (in order)

**ML layer first (no web dependencies):**
1. `requirements.txt` (ML deps only: torch, scikit-learn, pandas, requests)
2. `ml/__init__.py`, `ml/download_data.py`
3. `ml/dataset.py`, `ml/model.py`, `ml/train.py`, `ml/evaluate.py`, `ml/predict.py`

**Web layer after ML is verified:**

4. `requirements.txt` updated (add django, djangorestframework, django-cors-headers)
5. `core/settings.py`, `core/urls.py`
6. `gmail/auth.py`, `gmail/fetch.py`, `gmail/labels.py`
7. `dashboard/models.py`, `dashboard/serializers.py`
8. `dashboard/views.py` (DRF ViewSets), `dashboard/urls.py`
9. `dashboard/management/commands/scan_emails.py`
10. `frontend/` (Vite scaffold + pages + api client)

---

## Verification

**ML (must pass before web layer):**
1. `python -m ml.download_data` — `data/processed/emails.csv` exists with balanced classes
2. `python -m ml.train` — 10 epochs, loss decreases, `ml/model.pt` saved
3. `python -m ml.evaluate` — F1 ≥ 0.90 on test set
4. `python -m ml.predict "You have won a prize"` — returns scam=True, confidence > 0.8
5. `python -m ml.predict "Hi, meeting at 3pm"` — returns scam=False, confidence < 0.2

**Web layer:**
6. `python manage.py scan_emails` — authenticates with Gmail, scans, labels
7. `python manage.py runserver` + `npm run dev` — API on :8000, UI on :5173
8. Settings page: change scan window, save, verify it persists in DB
9. Reports page: shows daily/weekly/monthly summary after a scan run
10. "Scan Now" button triggers scan and updates email list
