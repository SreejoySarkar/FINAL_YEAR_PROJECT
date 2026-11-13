# Secure E-Voting System — Frontend

A professional React frontend for a Secure E-Voting & Corporate Polling System built on
**Django + Django REST Framework + PostgreSQL**. The frontend is a thin, role-aware client:
**all** security-critical work (authentication, QR token signing, eligibility, duplicate-vote
prevention, ballot sealing and result publication) happens on the Django backend.

## Tech stack

- React 19 (function components + hooks)
- Bootstrap 5 + custom CSS3 design system (navy / white / subtle green)
- Axios (centralised in `src/services/api.js`)
- React Router DOM (HashRouter, see note below)
- Lucide React (icons)
- Recharts (results charts)
- `qrcode` (renders the **server-issued** token payload as a QR image only)
- `html5-qrcode` (optional camera scanning, dynamically loaded)

## Folder structure

```
public/
src/
  assets/
  components/        Navbar, Sidebar, Footer, Loading, ProtectedRoute,
                     ElectionCard, CandidateCard, DashboardLayout, ui
  pages/             Home, Login, AdminDashboard, ElectionManagement,
                     CandidateManagement, VoterManagement, QRManagement,
                     AuditLogs, Results, VoterDashboard, QRVerification,
                     Voting, VoteConfirmation
  services/          api.js (axios + endpoint map), authService, electionService,
                     candidateService, voterService, qrService, votingService,
                     resultsService, ballotSession (memory-only), mockBackend (demo)
  context/           AuthContext.jsx
  styles/            global.css, dashboard.css, forms.css
  App.tsx  main.tsx  index.css
.env.example
```

> This repository **is** the frontend. If your monorepo keeps it beside the Django
> project, copy this folder to `frontend/` — nothing inside assumes the repo root.

## Running

```bash
# 1. install
npm install

# 2a. DEMO MODE (no backend needed — clearly labelled sample data)
npm run dev

# 2b. LIVE MODE (connect to your Django server)
cp .env.example .env
# edit .env → VITE_API_BASE_URL=http://127.0.0.1:8000
npm run dev
```

Production build: `npm run build` → `dist/` (single self-contained `index.html`).

### Demo mode accounts

| Role | Identifier | Password | Extra |
|---|---|---|---|
| Admin | `admin@securevote.org` | `Admin@123` | OTP `246810` (shown on screen, demo only) |
| Voter | `voter@securevote.org` | `Voter@123` | — |
| Voter (already voted) | `voter2@securevote.org` | `Voter@123` | to preview "already voted" state |

Demo QR verification tokens: `DEMO-VALID-TOKEN`, `DEMO-EXPIRED-TOKEN`, `DEMO-USED-TOKEN`.

Demo data is a preview aid. A persistent **DEMO MODE** banner is shown on every page, and
simulated votes/results are always labelled as samples — never presented as genuine.

## Connecting the Django backend

1. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL`.
2. **CORS** — allow the frontend origin in Django (using `django-cors-headers`):

```python
# settings.py
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + MIDDLEWARE
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",   # vite dev server
    "http://127.0.0.1:5173",
    # add your production frontend origin
]
```

3. Run both:

```bash
# terminal 1 — Django
python manage.py runserver 0.0.0.0:8000

# terminal 2 — React (another directory)
npm run dev
```

### API contract

**Note on endpoints:** the Django project itself is not part of this workspace, so its
`urls.py` could not be inspected. All paths the frontend calls are therefore declared in
**one place — `API_PATHS` in `src/services/api.js`** — following standard DRF conventions.
If your URL names differ, adjust them there (and the matching service function); no page
code changes are needed.

| Area | Method & path | Body | Expected response |
|---|---|---|---|
| Login | `POST /api/auth/login/` | `{identifier, password}` | `{token, user:{id,name,email,role,voter_id}}` **or** `{otp_required:true, otp_session, message}` |
| OTP verify | `POST /api/auth/otp/verify/` | `{code, otp_session?}` | `{token, user}` |
| Current user | `GET /api/auth/me/` | — | user object |
| Logout | `POST /api/auth/logout/` | — | `{ok:true}` |
| Admin stats | `GET /api/admin/stats/` | — | `{elections_total, elections_active, voters_total, candidates_total, votes_total}` |
| Elections | `GET/POST /api/elections/` · `GET/PATCH/DELETE /api/elections/{id}/` | `{title, description, starts_at, ends_at, status}` | election object(s); list items include `candidates_count`, `votes_cast` |
| Candidates | `GET/POST /api/candidates/` · `PATCH/DELETE /api/candidates/{id}/` · `GET /api/elections/{id}/candidates/` | `{name, role, description, election_id}` (+ `photo` multipart) | candidate objects |
| Voters | `GET /api/voters/?search=` · `POST /api/voters/` | `{name, voter_id, email, department, is_eligible}` | voter objects with `is_eligible`, `has_voted_elections` (titles only — **never** candidate choices) |
| QR generate | `POST /api/qr/generate/` | `{election_id}` | `{token, qr_payload, status, generated_at, expires_at, election_title}` — token **must be signed server-side** |
| QR verify | `POST /api/qr/verify/` | `{token, election_id}` | `{valid, reason: ok\|invalid\|expired\|used\|not_eligible\|already_voted\|election_not_active, message, verification_token?, voter_id?}` |
| Voter elections | `GET /api/voter/elections/` | — | elections available to the voter: `{id,title,description,starts_at,ends_at,status,eligible,has_voted,candidates_count}` |
| Submit vote | `POST /api/elections/{id}/vote/` | `{candidate_id, verification_token}` | `{success, reference_id}` |
| Results | `GET /api/elections/{id}/results/` | — | `{results_published, results_verified, status, total_votes, candidates:[{id,name,votes,percentage}], audit_summary}` |
| Audit logs | `GET /api/audit/logs/` | — | `[{id, at, actor, action, category, detail, status}]` |

**Authentication:** the frontend sends `Authorization: Bearer <token>` for every request,
so any DRF token scheme (simplejwt, `TokenAuthentication`, or a custom `token` field)
works out of the box. The login/OTP response must include the token in one of
`token` / `access` / `auth_token`. If you use Django **session auth** instead, remove the
interceptor in `api.js` and rely on `withCredentials` — but token auth is strongly
recommended for a voting system.

**Required backend behaviour** (the UI trusts these; it must not re-implement them):

- 401 for expired/invalid tokens, 403 for wrong roles on every protected endpoint.
- QR tokens signed, expiring and **single-use**; verification also re-checks voter
  eligibility and prior ballots.
- Vote endpoint re-validates eligibility, duplicate voting, token single-use and that the
  candidate belongs to the election; returns a receipt `reference_id`.
- Results endpoints return figures **only** when the election is closed, verified and
  published; voter endpoints never expose which candidate a voter chose.

## Security model (frontend side)

- Backend authorization is the real boundary; route protection in React is only a UX gate.
- The auth token is kept **in memory + sessionStorage** — never in localStorage.
- The ballot verification token and receipt reference live in an in-memory module
  (`services/ballotSession.js`); a page reload drops them by design.
- No crypto, signing, hashing or vote counting is performed in the browser.
- The chosen candidate is **never** persisted client-side and is **never displayed** after
  submission.
- 401 responses expire the session everywhere in one place (`setUnauthorizedHandler`).
- Network, validation, permission and timeout errors are mapped to safe, specific messages
  (`friendlyMessage` in `api.js`) — no stack traces or server internals are shown.

## Router note

`HashRouter` is used so the built single-file `dist/index.html` works on any static host
with no rewrite rules. For a conventional deployment where the server rewrites all paths
to `index.html`, swap `HashRouter` for `BrowserRouter` in `src/App.tsx`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Unable to reach the voting server…" | Django not running / wrong `VITE_API_BASE_URL`; restart `npm run dev` after editing `.env` |
| Login 401 with correct password | Check the login payload field names in `authService.js` match your serializer |
| Everything 403 as voter | Voter role name differs on your backend — `AuthContext` derives the role from `user.role` (fallback `is_staff`); adjust the field accordingly |
| Results always locked | The backend must set `results_published` + `results_verified` — by design the UI cannot bypass this |
