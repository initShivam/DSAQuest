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

The API uses DRF token authentication. New registrations receive a verification email, but email verification is not required before login. Users may sign in and use authenticated endpoints while `email_verified` is false. Verification remains available through the existing link and resend endpoints. After login, send:

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

The test suite covers generation idempotency, difficulty/fallback selection, duplicate completion rewards, goal and streak rules, authorization, timezone boundary behavior, email verification, resend delivery, password recovery, SMTP failures, and mocked HTTPS provider acceptance/rejection, timeout, rollback/retry, and log redaction. It never sends real emails.

## Production settings

Set `DJANGO_DEBUG=False`, a strong `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` (including `dsaquest.onrender.com`), and either `DATABASE_URL` or the `POSTGRES_*` variables. Configure `DJANGO_SECURE_SSL_REDIRECT=True`, secure cookies, HSTS, and `DJANGO_USE_HTTPS_PROXY=True` when TLS terminates at a trusted reverse proxy. The deployed settings include the known frontend origin `https://dsaquestt.vercel.app`; add any additional exact HTTPS origins through `CORS_ALLOWED_ORIGINS` and `DJANGO_CSRF_TRUSTED_ORIGINS`.

### Transactional email on Render free: Brevo HTTPS

Render free web services [block outbound SMTP ports 25, 465, and 587](https://render.com/docs/free#other-limitations). An `OSError: [Errno 101] Network is unreachable` during `socket.create_connection` happens before Gmail authentication; changing passwords, TLS, IPv4/IPv6 settings, or SMTP providers on the same ports does not remove this restriction. Gmail SMTP can remain enabled locally.

For Render free, use `accounts.email_backends.BrevoEmailBackend`. It sends the existing plain-text account emails through Brevo's [documented transactional HTTPS endpoint](https://developers.brevo.com/docs/send-a-transactional-email): `POST https://api.brevo.com/v3/smtp/email`, with `api-key` authentication. No provider SDK is used.

```text
PUBLIC_FRONTEND_URL=https://dsaquestt.vercel.app
PASSWORD_RESET_TIMEOUT=3600
EMAIL_BACKEND=accounts.email_backends.BrevoEmailBackend
BREVO_API_KEY=<private-brevo-api-key>
EMAIL_TIMEOUT=20
DEFAULT_FROM_EMAIL=<verified-sender-address>
```

`DEFAULT_FROM_EMAIL` must be a sender registered and verified in **your** Brevo account. Complete Brevo's account/transactional-sending approval and check available credits. Use a Brevo API key, not its SMTP key and not a Gmail App Password. `EMAIL_TIMEOUT` is the HTTP client's connect/read timeout, not a guarantee about end-to-end delivery time.

Brevo supports [sender verification by email](https://help.brevo.com/hc/en-us/articles/208836149-Create-a-new-sender-From-name-and-From-email) if the domain is not authenticated. You can investigate verifying your existing Gmail address there, but do not assume approval or deliverability: you cannot authenticate `gmail.com` yourself. For reliable production use, choose a domain you own and configure Brevo's required DNS authentication (DKIM/DMARC and any other records it specifies). Never use the Vercel or Render shared domain as though you own its email DNS.

The HTTPS backend does not require `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, or `EMAIL_USE_SSL`. Remove the unused Gmail password from Render after switching; keep it only in your local ignored environment if local SMTP is still needed. Remove obsolete `RESEND_API_KEY` and `EMAIL_PROVIDER` values too. Never set email credentials in Vercel or `VITE_*` variables.

### Local Gmail SMTP

Keep the SMTP values in `backend/.env.example` for local development. `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `smtp.gmail.com:587`, TLS on, SSL off, and your existing private Gmail App Password are still supported. TLS and SSL cannot both be enabled. Neither backend bypasses verification or changes the account model.

### Acceptance, delivery, and safe failure behavior

- All account emails still use `accounts/emailing.py` and Django `send_mail()`. There is no separate recovery email system or automatic fallback to SMTP.
- Only an HTTP **201** containing a nonempty `messageId` counts as Brevo acceptance. It is not proof of inbox delivery. Check Brevo's transactional **Delivered/Bounced/Blocked** events and a real mailbox after an authorized deployment. No delivery webhook or delivery-status database table was added.
- The existing generic HTTP 200 resend/reset responses deliberately do not reveal account existence or provider failures. They acknowledge the request, not successful delivery. No success/acceptance log is emitted for failed sends. The existing response strings remain unchanged for compatibility.
- Logs contain only fixed failure categories, exception class names, and HTTP status codes. They never include provider response bodies, exception messages/tracebacks, keys, recipient lists, token URLs, or email content. Inspect provider dashboard details privately; redact before sharing.
- Registration retains the existing atomic create-and-send behavior. An unacknowledged/failed send returns 503 and rolls back the new user; a retry can create one pending account. Database uniqueness still rejects duplicates. Sending an email never marks an account verified.
- HTTP requests have bounded connect/read timeouts, TLS certificate verification, redirects disabled, and no automatic retries. A timeout may mean the provider accepted a request but its acknowledgement was lost. Email submission and a database transaction cannot be committed atomically: a later DB failure/rollback can also leave an email pointing at an invalid link. Request a fresh link or retry as appropriate; exactly-once delivery would need a separately designed durable outbox and idempotency strategy, not database resets or fake migrations.

### Investigating the previous Resend 403

Do not assume a 403 is an SMTP/network problem or that another API key alone fixes it. Use the Resend request dashboard to inspect the failing operation's timestamp, HTTP status, and redacted error `name`/`message`. Compare with the [documented errors](https://resend.com/docs/api-reference/errors):

1. Testing-domain restrictions: the default testing sender can only mail your own account address. Other recipients require a verified domain.
2. Unverified/mismatched domain: the request's `from` domain must match a domain verified in the same Resend account. You cannot verify `gmail.com`, `vercel.app`, or `onrender.com` as your own domain.
3. Key/account permissions: check key activation, suspension, sending scope/domain restrictions, and account status. A sending-only key is sufficient for sending; do not grant full access merely to fix a send failure.

The exact previous 403 cause is unknown without that redacted provider diagnostic. Never dump request headers, request bodies, verification/reset links, or complete provider payloads into application logs. The Brevo transport does not reinstate Resend code or credentials.

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

For this email-only change, when you authorize a deployment:

1. Finish Brevo transactional account activation and verify the chosen sender/domain. Create a private API key in Brevo (never paste it into chat or source).
2. Set the Brevo environment block above in Render. Also set `DJANGO_LOAD_DOTENV=False`. Keep the existing Neon `DATABASE_URL`, Django signing key, and production security/CORS settings unchanged.
3. Remove any old SMTP/Resend credentials from Render; the Brevo path does not use them. Keep the existing Render working directory/build/start commands, installing the updated requirements.
4. Run `python manage.py check` and `python manage.py test` in a safe local/test environment. This change requires no migration, data repair, seed operation, reset, or fake migration.
5. Deploy only when authorized. With a mailbox you control, register, confirm that login is blocked before verification, open the verification link on the deployed frontend, then sign in. Check resend and password reset separately. Never copy token URLs into logs or tickets.
6. In Brevo's transactional dashboard, distinguish accepted requests from Delivered/Bounced/Blocked events. If HTTP errors occur, check sender approval, API key permissions, account activation, credits/rate limits, IP-access restrictions if enabled, and the provider status page privately. Render cold starts can still exceed the frontend's timeout; this transport cannot remove free-plan cold starts or quotas.

No Vercel source change is required: keep `VITE_API_URL=https://dsaquest.onrender.com/api`. Do not add email credentials to Vercel.

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
