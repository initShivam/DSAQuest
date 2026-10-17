# DSA Quest backend

This directory contains the self-contained Django + Django REST Framework MVP backend for DSA Quest. It implements the daily practice loop with curated question metadata and user-confirmed completion. LeetCode synchronization and code execution are intentionally out of scope.

## Local setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

SQLite is the default development database (`db.sqlite3`). PostgreSQL is supported by setting `DATABASE_URL=postgresql://user:password@host:5432/database`, or by setting `USE_POSTGRES=True` and the `POSTGRES_*` variables in `.env.example`. Environment variables must be supplied by the deployment environment; this project does not load or commit a `.env` file.

## Authentication

The API uses DRF token authentication. Register or log in, then send:

```text
Authorization: Token <token>
```

Registration and login return a token and user object:

```http
POST /api/auth/register/
Content-Type: application/json

{"email":"you@example.com","password":"a-strong-password","display_name":"You","timezone":"Asia/Kolkata","challenge_mode":"balanced"}
```

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

The test suite covers generation idempotency, difficulty/fallback selection, duplicate completion rewards, goal and streak rules, authorization, and timezone boundary behavior.
