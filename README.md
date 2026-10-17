# DSAQuest

DSAQuest is a focused daily practice dashboard for data structures and algorithms. It turns interview preparation into a repeatable loop:

**Sign in → receive a daily quest → solve on LeetCode → record completion → earn XP → maintain a streak → review progress.**

The current MVP uses a curated question catalog and user-reported completion. It links to official LeetCode problems, but it does not verify LeetCode submissions, execute code, or synchronize external accounts.

## What is included

- Email/password registration, login, logout, and profile preferences.
- Daily challenges with two mandatory questions and an optional bonus question.
- Difficulty modes: Beginner, Balanced, Intermediate, Advanced, and Adaptive.
- Curated questions grouped by DSA patterns and estimated solving time.
- Self-reported completion with optional personal notes.
- XP, levels, daily goals, current/longest streaks, and achievements.
- Progress charts, activity history, pattern coverage, and XP history.
- Responsive React dashboard with Light and Dark themes.
- Keyboard focus states, loading states, error recovery, reduced-motion support, and mobile navigation.

## Technology stack

### Frontend

- React 18
- TypeScript
- Vite
- Custom CSS design tokens and reusable UI functions in `frontend/src/App.tsx`
- Client-side History API routing (no React Router dependency)

### Backend

- Python 3
- Django 5
- Django REST Framework
- DRF token authentication
- SQLite for local development
- PostgreSQL support through environment configuration

### Main backend apps

- `accounts` — custom user model, authentication, and profile settings.
- `catalog` — questions, patterns, and question-pattern relationships.
- `challenges` — daily challenge generation and assignments.
- `progress` — completion records, streaks, XP, achievements, and analytics.

## Project structure

```text
.
├── backend/
│   ├── accounts/       # Users and authentication
│   ├── catalog/        # Questions, patterns, and seed data
│   ├── challenges/     # Daily challenge generation
│   ├── config/         # Django settings, URLs, ASGI/WSGI
│   ├── progress/       # XP, streaks, achievements, and history
│   ├── tests/          # Backend tests
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx     # App shell, routes, and reusable UI
│   │   ├── api.ts      # Typed API client
│   │   ├── auth.tsx    # Authentication context
│   │   └── styles.css  # Global styles and theme tokens
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
└── DSA_Quest_Professional_Implementation_Plan.md
```

## Prerequisites

Install the following before setting up the project:

- Python 3.10+ recommended.
- Node.js compatible with the installed Vite version: `^20.19.0 || >=22.12.0`.
- npm.
- A modern browser.
- Internet access if you want to open the external LeetCode links or load the hosted fonts.

PostgreSQL is optional. SQLite is used automatically when no PostgreSQL variables are configured.

## Local setup

The backend and frontend run as separate processes. Start the backend first, then start the Vite development server in a second terminal.

### 1. Set up the backend

PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Only needed on a fresh checkout:
Copy-Item .env.example .env
# Edit .env and set DJANGO_SECRET_KEY before continuing.
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000`. For PostgreSQL, set `USE_POSTGRES=True` and the real `POSTGRES_*` values in `.env`, or use a `DATABASE_URL`. The app will fail closed in production mode instead of silently using SQLite.

If PowerShell blocks virtual-environment activation, use a terminal with an appropriate execution policy or run the Python executable directly from `backend\.venv\Scripts\python.exe`.

### 2. Set up the frontend

Open a second terminal from the project root:

```powershell
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The Vite development server proxies `/api` requests to `http://localhost:8000`, so no frontend API URL is needed for local development.

### 3. Create an account

Use the registration screen to provide:

- Display name
- Email address
- Password of at least eight characters
- IANA timezone, for example `UTC`, `Asia/Kolkata`, or `America/New_York`
- Challenge mode

After registration, the dashboard creates or loads the challenge for the user’s current local date.

## Frontend commands

Run these commands from `frontend/`:

| Command | Purpose |
|---|---|
| `npm ci` | Install the locked frontend dependencies. |
| `npm run dev` | Start the Vite development server on port `5173`. |
| `npm run build` | Run TypeScript project checks and create a production build. |
| `npm run preview` | Preview the production build locally. |

There is currently no frontend test, lint, or format script configured.

## Backend commands

Run these commands from `backend/` with the virtual environment active:

| Command | Purpose |
|---|---|
| `python manage.py migrate` | Apply database migrations. |
| `python manage.py seed_data` | Insert or update the curated catalog and achievements. Safe to repeat. |
| `python manage.py runserver` | Start Django locally on port `8000`. |
| `python manage.py check` | Run Django configuration checks. |
| `python manage.py test` | Run the backend test suite. |

## Configuration

The backend loads `backend/.env` for local development using `python-dotenv`. Production deployments should inject secrets through the process environment or a secret manager; never commit the real `.env` file. `backend/.env.example` is a reference template only.

### Backend variables

| Variable | Description | Default |
|---|---|---|
| `DJANGO_SECRET_KEY` | Django signing key. Use a strong private value outside local development. | Required |
| `DJANGO_LOAD_DOTENV` | Loads `backend/.env` for local development. Disable it when deployment injects all variables directly. | `True` |
| `DJANGO_DEBUG` | Enables debug mode for values `1`, `true`, or `yes`. | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hostnames. Production must include `dsaquest.onrender.com`. | Required in production |
| `DATABASE_URL` | PostgreSQL URL beginning with `postgres://` or `postgresql://`. | SQLite |
| `USE_POSTGRES` | Enables the separate `POSTGRES_*` configuration when truthy. | Disabled |
| `POSTGRES_DB` | PostgreSQL database name. | — |
| `POSTGRES_USER` | PostgreSQL user. | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password. | Empty |
| `POSTGRES_HOST` | PostgreSQL host. | `localhost` |
| `POSTGRES_PORT` | PostgreSQL port. | `5432` |
| `DJANGO_USE_HTTPS_PROXY` | Trust `X-Forwarded-Proto` from a TLS-terminating reverse proxy. | `False` |
| `DJANGO_SECURE_SSL_REDIRECT` | Redirect HTTP to HTTPS. Defaults to enabled when debug is off. | Depends on `DJANGO_DEBUG` |
| `DJANGO_SESSION_COOKIE_SECURE` | Send Django admin/session cookies only over HTTPS. | Depends on `DJANGO_DEBUG` |
| `DJANGO_CSRF_COOKIE_SECURE` | Send CSRF cookies only over HTTPS. | Depends on `DJANGO_DEBUG` |
| `DJANGO_SECURE_HSTS_SECONDS` | HSTS duration in seconds. | `31536000` when debug is off, otherwise `0` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated HTTPS origins allowed for CSRF-protected requests. | Empty |
| `CORS_ALLOWED_ORIGINS` | Exact frontend origins allowed to call `/api/`. | Empty |

Example PowerShell configuration:

```powershell
$env:DJANGO_SECRET_KEY = "replace-with-a-long-random-secret"
$env:DJANGO_DEBUG = "False"
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1"
$env:DATABASE_URL = "postgresql://postgres:password@localhost:5432/dsa_quest"
```

### Frontend variables

`VITE_API_URL` is read at build time by `frontend/src/api.ts`.

```powershell
$env:VITE_API_URL = "https://api.example.com/api"
npm run build
```

If it is not set, the frontend uses `/api`, which works with the Vite development proxy and with a same-origin deployment. A separate API origin should be set to `https://dsaquest.onrender.com/api`; a host-only value is normalized to that API path. The backend allows the exact frontend origin `https://dsaquestt.vercel.app` and additional origins must be listed explicitly in `CORS_ALLOWED_ORIGINS`.

## Frontend routes

The frontend uses the browser History API and renders these paths from the app shell:

| Path | Screen |
|---|---|
| `/` | Dashboard overview |
| `/quest` | Daily Quest |
| `/patterns` | Pattern progress and question catalog |
| `/progress` | Activity charts and difficulty metrics |
| `/achievements` | Achievement progress |
| `/history` | Completion and XP history |
| `/profile` | Profile and challenge preferences |

The frontend stores the DRF token in browser `localStorage` under `dsa-quest-token` and the selected theme under `dsa-quest-theme`.

## API overview

The backend exposes the API under `/api/`. Authentication and login endpoints are public; user-specific endpoints require a token.

Send the token using:

```http
Authorization: Token <token>
```

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register/` | Create an account. Returns `{token, user}`. |
| `POST` | `/api/auth/login/` | Authenticate with email and password. |
| `POST` | `/api/auth/logout/` | Delete the current user token. |
| `GET` | `/api/auth/me/` | Read the authenticated profile. |
| `PATCH` | `/api/auth/me/` | Update display name, timezone, or challenge mode. |

Registration example:

```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "a-strong-password",
  "display_name": "You",
  "timezone": "Asia/Kolkata",
  "challenge_mode": "balanced"
}
```

### Dashboard and challenge endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/` | User summary, level, streak, practiced patterns, and today’s challenge. |
| `GET` | `/api/challenges/today/` | Get or create the challenge for the user’s local date. |
| `POST` | `/api/challenges/generate/` | Idempotently get or create the same local-date challenge. |

### Catalog and completion endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/questions/` | Active question catalog. Supports `difficulty`, `pattern`, and `ordering`. |
| `GET` | `/api/questions/{id}/` | Read one active question. |
| `POST` | `/api/questions/{id}/complete/` | Record completion, optionally with `personal_notes`. |
| `GET` | `/api/patterns/` | List patterns with available and completed counts. |
| `GET` | `/api/patterns/{id}/` | Read one pattern. |

Completion notes are limited to 5,000 characters. A question can only be completed when it is assigned in the user’s current local-day challenge.

### Progress endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/progress/` | XP, level, completions, streaks, difficulty counts, and pattern count. |
| `GET` | `/api/progress/history/?days=30` | Daily activity and completed-question history. `days` is clamped to 1–366. |
| `GET` | `/api/achievements/` | Achievement definitions, unlock state, and progress. |
| `GET` | `/api/streak/` | Current and longest streak details. |
| `GET` | `/api/xp/history/` | XP total and transaction ledger. |

List endpoints use Django REST Framework page-number pagination with a default page size of 50. The frontend follows paginated `next` links when loading catalog data.

## Business rules

- Beginner assigns Easy + Easy.
- Balanced assigns Easy + Medium.
- Intermediate assigns Medium + Medium.
- Advanced assigns Medium + Hard, using safe fallback selection when the catalog is sparse.
- Adaptive currently behaves as Easy + Medium; it is not yet progress-adaptive.
- A daily quest normally has two mandatory assignments and may include one bonus assignment.
- Easy, Medium, and Hard completions award 10, 25, and 50 XP respectively.
- Completing both mandatory assignments awards a one-time 20 XP daily-goal bonus.
- Bonus assignments award question XP but do not complete the daily goal by themselves.
- Repeating a completion returns `duplicate: true` and does not award duplicate XP.
- The current streak advances only on goal-qualified local dates.
- Timestamps are stored in UTC; challenge and activity dates use the user’s IANA timezone.
- Completion is self-reported and is not verified against LeetCode.

## Data and persistence

The main domain models are:

- `accounts.User`
- `catalog.Question`
- `catalog.Pattern`
- `catalog.QuestionPattern`
- `challenges.DailyChallenge`
- `challenges.DailyChallengeQuestion`
- `progress.UserQuestionProgress`
- `progress.DailyActivity`
- `progress.XPTransaction`
- `progress.Achievement`
- `progress.UserAchievement`
- `progress.UserPatternProgress`

Challenge creation and completion rewards run inside database transactions. Uniqueness constraints and idempotency keys protect daily challenges, activity summaries, progress, achievements, and XP transactions from duplicate writes.

## Verification

From `backend/`:

```powershell
python manage.py check
python manage.py test
```

From `frontend/`:

```powershell
npm run build
```

The backend tests cover challenge idempotency, difficulty and fallback selection, duplicate completion rewards, daily-goal and streak rules, authorization, and timezone boundaries. The frontend build runs the TypeScript project checks before producing the Vite bundle.

## Deployment notes

Before deploying:

1. Set a strong `DJANGO_SECRET_KEY`.
2. Set `DJANGO_DEBUG=False`.
3. Restrict `DJANGO_ALLOWED_HOSTS` to real hosts.
4. Use PostgreSQL or another managed database instead of the development SQLite file.
5. Serve the frontend build from `frontend/dist`.
6. Configure the static host to fall back to `index.html` for `/quest`, `/patterns`, `/progress`, `/achievements`, `/history`, and `/profile`.
7. Set `VITE_API_URL` during the frontend build if the API is hosted on a different origin.
8. Configure CORS and HTTPS when frontend and API are deployed separately.
9. Do not commit database files, tokens, passwords, or environment secrets.

The project does not currently include Docker, Celery, Redis, a scheduled challenge worker, frontend browser tests, or automatic LeetCode synchronization.

## Troubleshooting

### The dashboard says the API is unavailable

Confirm that Django is running on port `8000` and that the frontend is running through Vite on port `5173`. The local proxy only works when the frontend is started with `npm run dev`.

### The database has no questions

Run the migrations and seed command again:

```powershell
cd backend
python manage.py migrate
python manage.py seed_data
```

### Refreshing a frontend route returns a 404 in production

Configure the web server to serve `frontend/dist/index.html` for unknown application paths. The frontend uses client-side History API routing.

### PostgreSQL connection errors

Check `DATABASE_URL`, or set `USE_POSTGRES=True` together with `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT`. Ensure PostgreSQL is running and reachable before running migrations.

## Scope and future work

The MVP intentionally keeps the core loop small and reliable. The following are not implemented yet:

- Verified LeetCode submission synchronization.
- In-app code execution.
- Scheduled/background challenge generation.
- Progress-adaptive challenge selection.
- Weekly-goal XP and streak freezes.
- Social leaderboards, tournaments, or AI-generated explanations.

See `DSA_Quest_Professional_Implementation_Plan.md` for the broader product and technical planning document.
