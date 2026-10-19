# DSA Quest backend

This directory contains the self-contained Django + Django REST Framework MVP backend for DSA Quest. It implements the daily practice loop with curated question metadata and user-confirmed completion. LeetCode synchronization and code execution are intentionally out of scope.

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Only needed on a fresh checkout:
Copy-Item .env.example .env
# Fill in DJANGO_SECRET_KEY, database values, and Gmail SMTP values in .env.
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

SQLite is available for local development when PostgreSQL variables are not configured. PostgreSQL is selected by setting `DATABASE_URL=postgresql://user:password@host:5432/database`, or by providing `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, and `POSTGRES_PORT` in `.env`. The settings load `backend/.env` for local development without committing it; production should inject secrets through the deployment environment or a secret manager. When `DJANGO_DEBUG=False`, the app requires a non-wildcard `DJANGO_ALLOWED_HOSTS` value and a PostgreSQL database.

## Authentication

The API uses DRF token authentication. New registrations must verify their email before login. After verification, log in and send:

```text
Authorization: Token <token>
```

Registration returns a generic verification-required response. Login returns a token and user object:

```http
POST /api/auth/register/
Content-Type: application/json

{"email":"you@example.com","password":"a-strong-password","confirm_password":"a-strong-password","display_name":"You","timezone":"Asia/Kolkata","challenge_mode":"balanced"}
```

Authentication recovery endpoints:

- `POST /api/auth/email/verify/` with `uid` and `token` from the verification link.
- `POST /api/auth/email/resend/` with an email address. The response is generic to avoid account enumeration.
- `POST /api/auth/password-reset/request/` with an email address. The response is generic to avoid account enumeration.
- `POST /api/auth/password-reset/confirm/` with `uid`, `token`, `new_password`, and `confirm_password`.

Verification and reset links are generated for `PUBLIC_FRONTEND_URL`. Password reset links use Django's signed password-reset token generator and expire after `PASSWORD_RESET_TIMEOUT` seconds. Verification links use a signed Django token and become invalid once the account is verified.

## API surface

- `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/logout/`, `GET/PATCH /api/auth/me/`
- `GET /api/dashboard/`
- `GET /api/challenges/today/`, `POST /api/challenges/generate/`
- `GET /api/questions/`, `GET /api/questions/{id}/`, `POST /api/questions/{id}/complete/`
- `GET /api/progress/`, `GET /api/progress/history/`
- `GET /api/patterns/`, `GET /api/patterns/{id}/`
- `GET /api/achievements/`, `GET /api/streak/`, `GET /api/xp/history/`

Question completion is accepted only for a question assigned in the user's current local-day challenge. A completion is self-reported and is not a verified LeetCode submission.

## Reliability rules

- `DailyChallenge(user, challenge_date)`, `DailyActivity(user, activity_date)`, user progress, pattern progress, achievements, and XP idempotency keys have database uniqueness constraints.
- Challenge creation and completion rewards run inside atomic transactions.
- Repeating a completion request returns `duplicate: true` and awards no additional XP.
- The question reward is 10/25/50 XP for easy/medium/hard; completing the two-question daily goal adds 20 XP once.
- Timestamps are stored in UTC and activity/challenge dates are derived from the user's IANA timezone. Historical activity dates are retained if a user changes timezone; only future local-date calculations use the new setting.
- Current streaks count consecutive goal-qualified local dates, using yesterday as the latest qualifying date when today is not complete.

## Checks

```powershell
python manage.py check
python manage.py test
```

The test suite covers generation idempotency, difficulty/fallback selection, duplicate completion rewards, goal and streak rules, authorization, timezone boundary behavior, email verification, resend delivery, password recovery, and SMTP failure handling.

## Production settings

Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` (including `dsaquest.onrender.com`), and either `DATABASE_URL` or the `POSTGRES_*` variables. Configure `DJANGO_SECURE_SSL_REDIRECT=True`, secure cookies, HSTS, and `DJANGO_USE_HTTPS_PROXY=True` when TLS terminates at a trusted reverse proxy. The deployed settings include the known frontend origin `https://dsaquestt.vercel.app`; add any additional exact HTTPS origins through `CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

Email delivery uses Django's SMTP backend. Configure Gmail SMTP locally and on Render, and never commit the app password:

```text
PUBLIC_FRONTEND_URL=https://dsaquestt.vercel.app
PASSWORD_RESET_TIMEOUT=3600
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=gharkatvid1@gmail.com
EMAIL_HOST_PASSWORD=<gmail-app-password>
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_TIMEOUT=20
DEFAULT_FROM_EMAIL=gharkatvid1@gmail.com
```

Use either TLS or SSL, not both. Render must receive these values in its environment settings. Automated tests override Django's email backend with the in-memory backend; a real Gmail mailbox is required for end-to-end production verification.

## Render deployment

Create the Render web service from the repository root, then set its **Root Directory** to `backend`. If the service supports a pre-deploy command, use:

```text
Build Command: pip install -r requirements.txt
Pre-deploy Command: python manage.py migrate
Start Command: gunicorn --bind 0.0.0.0:$PORT config.wsgi:application
```

On Render's free plan, where the pre-deploy command is unavailable, keep the same build command and use this **Start Command** instead:

```sh
python manage.py migrate --noinput && gunicorn --bind 0.0.0.0:$PORT config.wsgi:application
```

The `&&` is Render's Linux shell syntax: Gunicorn starts only if migrations succeed. Both commands run from `backend/` with the same service environment and `config.settings`, so they use the same database configuration. Keep `DJANGO_SETTINGS_MODULE` unset or set to `config.settings`, and do not provide a separate database override just for migrations. Do not run migrations during the dependency build or generate migrations on Render.

This fallback runs the migration check on each start. Applied migrations are not reapplied. For multiple instances or future schema changes requiring a coordinated rollout, use a single migration job before starting the new application instances rather than concurrent startup migrations.

If the Render service keeps the repository root as its working directory, use `pip install -r backend/requirements.txt` instead, but setting the root directory to `backend` is recommended. Add `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS=dsaquest.onrender.com`, `DATABASE_URL`, and `DJANGO_USE_HTTPS_PROXY=True` in Render's environment settings. The API URL used by Vercel should be `https://dsaquest.onrender.com/api` (the frontend also normalizes the host-only value to this path).

### Migration verification and missing user table

`accounts/migrations/0001_initial.py` already creates the custom `accounts.User` model and its `accounts_user` table. Do not generate a replacement migration merely because the production table is missing.

Before repairing a missing table, use the deployed service's environment to confirm the intended Neon branch/database privately, inspect the PostgreSQL schema read-only (including `search_path`), and compare it with:

```sh
python manage.py showmigrations accounts
python manage.py showmigrations
python manage.py migrate --plan
```

If a migration is recorded as applied but its table is absent, or its table exists without the corresponding migration record, stop and investigate the mismatch. Do not reset the database, manually create tables, or use `--fake` / `--fake-initial` as a shortcut. Take a recoverable backup before an approved production migration.

After a successful deployment, `showmigrations accounts` should show `[X] 0001_initial`. Check for pending migrations with `python manage.py migrate --check` and confirm that the user table is visible to the runtime database connection; the migration record alone does not prove the schema exists. Finally, verify `POST /api/auth/login/` with an existing valid account and check that Render no longer reports `relation "accounts_user" does not exist`. Migrations create schema, not user accounts, so a new database still requires registration.
