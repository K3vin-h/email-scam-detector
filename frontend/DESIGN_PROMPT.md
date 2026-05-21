# Claude Design Prompt — Scam Filter Frontend

## Role & Context

You are redesigning the UI of **Scam Filter**, a local macOS dashboard that connects to Gmail via OAuth, scans incoming emails with a PyTorch neural network, and flags scam messages. The app is built with **React + Vite + Tailwind CSS**. All output must be valid JSX with Tailwind utility classes — no CSS-in-JS, no styled-components, no inline `style` props.

The current UI is functional but visually generic (flat slate cards, uniform spacing, no hierarchy). The redesign should feel like a polished, opinionated SaaS product, not a template.

---

## Visual Direction

**Style:** Modern light glassmorphism with strong typographic hierarchy.

### Core Aesthetic
- **Background:** Full-page gradient — `from-slate-50 via-indigo-50/40 to-slate-100` or similar cool-light wash. Not pure white.
- **Cards:** Frosted glass — `bg-white/70 backdrop-blur-md border border-white/60 shadow-xl shadow-slate-200/50 rounded-2xl`. Cards should feel like they float above the background.
- **Surface layering:** Background → page gradient, Layer 1 → section containers, Layer 2 → cards, Layer 3 → interactive elements (inputs, badges).

### Color Palette
| Token | Usage | Example Tailwind |
|-------|-------|-----------------|
| Scam / danger | Scam emails, error states, high-risk indicators | `rose-500`, `rose-50`, `rose-200` |
| Legit / safe | Legitimate emails, success states | `emerald-500`, `emerald-50`, `emerald-200` |
| Accent | Active states, focus rings, primary actions | `indigo-500`, `indigo-600`, `violet-500` |
| Neutral | Text, borders, backgrounds | `slate-900` (heading), `slate-600` (body), `slate-300` (dividers) |

### Typography
- Font: **Inter** (already loaded) — geometric, clean.
- Metric numbers: `text-4xl font-bold tracking-tight tabular-nums` — large, bold, designed.
- Section headings: `text-lg font-semibold text-slate-800`
- Body / labels: `text-sm text-slate-500`
- No generic gray-on-white text stacks — every text element should have a clear hierarchy role.

### Interactions
- Cards: `transition-all hover:-translate-y-0.5 hover:shadow-2xl` — subtle lift on hover.
- Buttons: `transition-all active:scale-95` — physical press feel.
- Status badges: `transition-colors duration-200`
- Scan button: animated ring pulse while scanning (`animate-ping` ring variant).
- Segmented controls (FilterBar): smooth `transition-transform` slide for the active indicator pill.

---

## Page Specs

### 1. LoginPage (`/login`)

**Layout:** Full-viewport centered, gradient background.

**Elements:**
- Background: gradient blob or mesh pattern using indigo/violet tones — not flat.
- Centered card (max-w-sm, glassmorphism): 
  - Shield or scan icon at top (large, indigo-colored SVG)
  - `h1`: "Scam Filter" — bold, large
  - Subheading: "Gmail scam detection, locally hosted" — slate-500, small
  - "Sign in with Google" button: full-width, pill-shaped (`rounded-full`), indigo gradient background or white with Google icon, prominent
  - Subtle "Protected by local AI" footnote

**Mood:** Clean, trustworthy, minimal. Makes the user feel secure before they log in.

---

### 2. DashboardPage (`/`)

**Layout:** Sticky NavBar + scrollable main content in a `max-w-5xl mx-auto px-6` container.

**Stat Cards Row (3 cards, equal width):**
Each card uses glassmorphism. Content per card:
- **Emails Scanned** — total count, slate/indigo color, inbox icon
- **Scams Found** — count, rose color, shield-alert icon
- **Scan Rate** — percentage of scams, amber or violet, chart icon

Display: Large `text-4xl font-bold` number, small label below, subtle icon top-right corner of card.

**Scan Now Button:**
- Below stat cards, right-aligned or centered
- Pill shape, indigo-to-violet gradient background, white text, `font-semibold`
- Loading state: `animate-spin` spinner + "Scanning…" text
- After scan: result summary appears inline ("Found 3 scams in 42 emails") with fade-in

**FilterBar (segmented control):**
- Container: `bg-slate-100/80 rounded-full p-1 inline-flex`
- Active pill: `bg-white rounded-full shadow-sm` with smooth slide transition
- Options: "All", "Scam only", "Legit only"

**Email List:**
- Replace flat rows with subtle card-like rows: `bg-white/60 backdrop-blur-sm border-b border-slate-100`
- Left accent: 3px colored left border — rose for scam, emerald for legit (`border-l-4`)
- Sender avatar: circle with initials (`w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold`)
- Subject + snippet: subject in `font-medium text-slate-800`, snippet in `text-slate-400 text-xs truncate`
- Status badge: pill-shaped, colored (`bg-rose-50 text-rose-600 border border-rose-200` for scam)
- Confidence: thin horizontal pill `w-16 h-1.5 rounded-full` — rose or emerald fill
- Date: right-aligned, `text-xs text-slate-400`

**Pagination:**
- Centered below list
- Previous / Next as icon buttons (`rounded-full border`) + page info text in between

---

### 3. ReportsPage (`/reports`)

**Layout:** Same max-w-5xl container. Period filter at top, then card grid.

**Period Filter:** Same segmented control pattern as FilterBar — "All", "Daily", "Weekly", "Monthly".

**Report Cards (2-column grid, `gap-4`):**
Each card (glassmorphism):
- Top-left: period badge — colored pill (`bg-violet-50 text-violet-700` for weekly, `bg-amber-50 text-amber-700` for daily, etc.)
- Center: large scam count (`text-5xl font-bold text-rose-500`) — this is the hero number
- Below count: label "scams detected"
- Divider line
- "Top Senders" section: ranked list, each row has sender address + small horizontal bar showing relative count (CSS width, not a chart library)
- Bottom: `generated_at` timestamp in `text-xs text-slate-400`

**Empty state:** If no reports, centered illustration + "No reports yet — run a scan to generate your first report."

---

### 4. SettingsPage (`/settings`)

**Layout:** Centered `max-w-2xl mx-auto` form card (glassmorphism).

**Grouped sections inside the card:**

**Section 1 — Scan Schedule**
- `scan_window_days`: number input with label "Scan window" + helper text "Days of email history to include"
- `scan_frequency_hours`: number input (1–168) with label "Scan frequency" + helper text "Hours between automatic scans"

**Section 2 — Notifications**
- `notify_frequency`: styled `<select>` dropdown — "Daily", "Weekly", "Monthly"
- `notify_via_email`: toggle switch (`rounded-full` track, indigo when on) + label "Email notifications"
- `notify_email_address`: text input, only visible when toggle is on (smooth `height` transition or conditional render with fade)

**Section 3 — Gmail Integration**
- Read-only status block: shows connected Gmail account or "Not connected"
- "Reconnect Gmail" secondary button if needed

**Save Button:**
- Full-width at bottom of card, indigo gradient, pill shape
- Loading spinner during save
- Toast notification: emerald for success, rose for error — appears top-right corner, auto-dismisses after 3s

**Input Styling:**
- `bg-white/80 backdrop-blur-sm border border-slate-200 rounded-xl px-4 py-2.5`
- Focus: `ring-2 ring-indigo-400 border-indigo-300 outline-none`

---

## NavBar

**Sticky top, full-width:**
- Background: `bg-white/80 backdrop-blur-md border-b border-slate-200/60`
- Left: "Scam Filter" logo (shield icon + bold text)
- Center or right: nav links — Dashboard, Reports, Settings
- Active link: indigo underline accent or indigo text weight
- No hamburger menus — desktop-first, simple horizontal layout

---

## Component Redesign Inventory

Redesign each of these existing components. Keep their props and data shapes unchanged — only update the JSX and Tailwind classes:

| Component | Current | Target |
|-----------|---------|--------|
| `NavBar` | White sticky bar, plain links | Frosted glass bar, indigo active state |
| `StatCard` | Flat white card, simple number | Glassmorphism card, icon, color-coded |
| `EmailRow` | Plain `<tr>` rows | Frosted row with left accent border, avatar initials |
| `FilterBar` | Button group with border | Segmented control with sliding pill |
| `Pagination` | Text + Previous/Next buttons | Rounded icon buttons + page info |
| `ScanButton` | Plain button | Gradient pill, pulse animation during scan |
| `ReportCard` | Flat white card | Glassmorphism, hero scam number, sender bars |

---

## Hard Constraints

1. **Output JSX only** — Tailwind utility classes exclusively. No `style={{}}` props, no CSS modules, no styled-components.
2. **Preserve all data fields** — do not remove any information currently displayed (senders, subjects, confidence scores, timestamps, top senders, etc.)
3. **No new dependencies** — Tailwind and React only. No chart libraries, no animation libraries, no icon packs beyond what's already used (inline SVGs are fine).
4. **Maintain accessibility** — keep `aria-pressed`, `aria-label`, `role="group"`, `role="alert"`, `htmlFor` attributes. Add any missing ones.
5. **Light mode only** — no dark mode toggle. The glassmorphism direction requires a light background to work.
6. **Same routing** — `/`, `/login`, `/reports`, `/settings` routes unchanged.
7. **Same API shapes** — props match the existing Django API responses: `{ sender, subject, snippet, is_scam, confidence, received_at }` for emails, etc.
