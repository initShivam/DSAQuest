# DSA Quest — Product & Implementation Plan

**Document type:** Product Requirements and Technical Implementation Plan  
**Status:** Draft for MVP planning  
**Version:** 1.0  
**Last updated:** 15 October 2026  
**Working product name:** DSA Quest

---

## 1. Executive Summary

DSA Quest is a gamified web application designed to make daily Data Structures and Algorithms (DSA) practice more consistent and engaging. It combines curated LeetCode problem links, daily challenges, streaks, XP, achievements, pattern-based learning, and progress history.

The product’s primary objective is to help users build a sustainable DSA practice habit while developing stronger problem-solving skills for technical interviews and placements.

The MVP will focus on a reliable daily practice loop:

**Sign in → Receive two daily questions → Solve and record progress → Earn XP → Maintain streak → Review progress.**

The first release will use a curated question catalog and user-confirmed completion. Automatic LeetCode submission synchronization and in-app code execution are explicitly out of scope until a supported, reliable integration is verified.

## 2. Product Vision and Goals

### Vision

Make DSA practice feel like a clear, rewarding daily quest rather than an unstructured list of problems.

### Product goals

1. Encourage users to solve at least two qualifying questions each day.
2. Organize questions by difficulty, topic, and problem-solving pattern.
3. Make progress, consistency, and areas for improvement visible.
4. Use rewards to reinforce genuine learning activity—not clicks or repeated completion events.
5. Support a maintainable architecture that can grow without premature infrastructure complexity.

### Non-goals for the MVP

- Building a replacement for LeetCode.
- Hosting or executing arbitrary user-submitted code.
- Assuming unrestricted access to an official LeetCode submission API.
- Building microservices or deploying Kubernetes before measured demand requires it.
- Adding AI-generated explanations, social leaderboards, or tournaments before the core learning loop works.

## 3. Target Users and Primary Use Case

### Primary user

A student or early-career developer preparing for coding interviews who finds conventional DSA practice difficult to sustain.

### Main user journey

1. The user registers and selects a difficulty mode and timezone.
2. The dashboard displays today’s assigned challenge and daily goal.
3. The user opens each problem on LeetCode.
4. The user returns to DSA Quest and records completion.
5. The backend validates the action and updates progress, XP, streaks, and eligible achievements.
6. The dashboard refreshes to show the new state.
7. The user reviews past activity and pattern progress.

**Trust principle:** In the MVP, user-confirmed completion is self-reported. The application must not label it as a verified LeetCode submission.

## 4. Functional Requirements

### 4.1 Authentication and Profile

- User registration, login, and logout.
- Secure password handling through Django’s authentication system.
- User profile with display name, selected challenge mode, and IANA timezone.
- Authorization checks for every user-specific endpoint.
- A defined policy for timezone changes so historical streaks are not silently rewritten.

### 4.2 Question Catalog

Each question should have:

- Internal ID and unique slug.
- Title.
- Official LeetCode problem URL.
- Difficulty: Easy, Medium, or Hard.
- One or more associated DSA patterns.
- Estimated solving time, where available.
- Active/inactive status.
- Catalog validation timestamp, if automated validation is implemented.

Use a many-to-many relationship between questions and patterns because one problem can exercise multiple patterns.

Maintain a curated, verified catalog for the MVP. Review applicable terms and licensing before copying problem statements, editorial solutions, or other protected content. Prefer official links and original learning notes.

### 4.3 Daily Challenges

- Create one daily challenge per user-local calendar date.
- Assign two mandatory questions by default.
- Allow one optional bonus question.
- Prevent duplicate question assignment within a challenge unless the item is explicitly a revision task.
- Exclude completed and recently assigned questions where suitable alternatives exist.
- Provide a safe fallback if the catalog does not contain enough eligible questions.
- Generate challenges through a scheduled task and an idempotent on-demand fallback.
- Display question title, difficulty, pattern, estimated time, XP reward, status, and a **Solve on LeetCode** action.

#### Suggested challenge modes

| Mode | Mandatory questions | Intended use |
|---|---|---|
| Beginner | Easy + Easy | Build fundamentals |
| Balanced (default) | Easy + Medium | Consistent general practice |
| Intermediate | Medium + Medium | Pattern development |
| Advanced | Medium + Hard | Interview challenge |
| Adaptive | Selected using available progress data | Personalized practice |

The optional third question is a bonus and does not count toward the mandatory daily goal.

### 4.4 Completion Tracking

- Record question status and completion timestamps.
- Separate a user’s overall question progress from a specific daily assignment.
- Allow a previously solved question to appear later as an explicit revision task.
- Prevent repeated requests from awarding duplicate XP.
- Clearly distinguish self-reported completion from verified submission data.
- Keep personal notes optional.

### 4.5 Daily Goal and Streaks

- Default goal: two qualifying question completions per local calendar day.
- One completion shows partial progress; two qualifying completions complete the daily goal.
- The streak advances only when the daily goal is met.
- A missed qualifying day breaks the current streak according to the documented rule.
- Calculate streaks on the server using the user’s configured timezone.
- Store timestamps in UTC and derive local activity dates consistently.
- Enforce one activity summary per user per local date.

A streak-freeze feature is deferred until after the MVP.

### 4.6 XP and Levels

Suggested starting reward values:

| Event | XP |
|---|---:|
| Easy question completed | 10 |
| Medium question completed | 25 |
| Hard question completed | 50 |
| Daily goal completed | 20 bonus |
| Weekly goal completed | 50 bonus |
| Verified first-attempt acceptance | 5 bonus, only if trustworthy attempt data exists |

These values are initial product settings, not fixed business rules. Review them against real usage and ensure users cannot farm XP by repeatedly marking the same activity complete.

Use an append-only XP transaction ledger as the auditable source of reward events. A cached total may be maintained for display, but it must be reconcilable against the ledger.

Suggested illustrative levels:

| Level | XP range | Title |
|---|---:|---|
| 1 | 0–99 | Beginner |
| 2 | 100–249 | Apprentice |
| 3 | 250–499 | Problem Solver |
| 4 | 500–999 | Pattern Hunter |
| 5 | 1,000–1,999 | Code Warrior |
| 6 | 2,000+ | DSA Master |

### 4.7 Achievements

Initial achievement candidates:

| Achievement | Unlock condition |
|---|---|
| First Blood | Complete the first question |
| Getting Started | Complete 10 questions |
| Week Warrior | Meet the daily goal for 7 consecutive days |
| Pattern Hunter | Practice 5 distinct patterns |
| Easy Explorer | Complete 25 Easy questions |
| Medium Crusher | Complete 25 Medium questions |
| Hard Challenger | Complete 10 Hard questions |
| Consistency King | Reach a 30-day qualifying streak |
| Revision Master | Complete 20 revision tasks |
| Century Club | Complete 100 questions |

Achievement conditions must be evaluated on the server and each achievement must unlock at most once per user. Show both locked and unlocked achievements, with clear progress toward the next milestone where possible.

### 4.8 Pattern-Based Learning

Initial pattern taxonomy:

1. Arrays and Strings
2. Hashing
3. Two Pointers
4. Sliding Window
5. Sorting
6. Binary Search
7. Linked Lists
8. Stacks and Queues
9. Recursion and Backtracking
10. Trees and Binary Search Trees
11. Heaps and Priority Queues
12. Graphs (BFS/DFS)
13. Greedy Algorithms and Intervals
14. Dynamic Programming
15. Tries
16. Advanced Graphs
17. Bit Manipulation

The taxonomy can be refined as the catalog grows. Do not require users to follow a rigid linear sequence.

Each pattern page should display:

- Questions completed versus available.
- Difficulty breakdown.
- Recently practiced date.
- Attempt and correctness statistics, if trustworthy data exists.
- Recommended next problem.
- Revision items due.

In the MVP, use **Pattern Progress** rather than claiming a precise **Mastery Score**. A mastery score should only be introduced when the system has enough reliable evidence about correctness, independent solving, and revision performance. Self-reported completion alone cannot establish mastery.

### 4.9 Progress History and Analytics

- Calendar heatmap showing daily activity.
- Daily goal completion history.
- Question history with title, date, difficulty, pattern, status, and XP.
- Weekly and monthly summaries.
- Pattern coverage and difficulty distribution.
- Clear empty, loading, and error states.

Do not imply accepted-submission accuracy or actual solve time unless the data source supports those metrics.

## 5. Dashboard and UX Requirements

### Design direction

- Dark, modern, coding-focused interface.
- Clear typography and strong visual hierarchy.
- Subtle gradients and restrained motion.
- Accessible contrast and keyboard navigation.
- Responsive layouts for desktop, tablet, and mobile.
- Fast initial load and minimal unnecessary animation.

### Dashboard sections

1. **Navigation:** Dashboard, Daily Quest, Patterns, Progress, Achievements, History, Profile.
2. **Welcome panel:** User greeting, current level, XP progress, and a clear next action.
3. **Today’s Quest:** Two mandatory questions, optional bonus, and completion progress.
4. **Summary cards:** Current streak, questions completed, total XP, and patterns practiced.
5. **Weekly activity:** Calendar heatmap and daily-goal status.
6. **Pattern progress:** Progress cards for the user’s active patterns.
7. **Achievements:** Recent unlocks and next milestones.
8. **Recent activity:** Latest completions and links to question notes or revision items.

The daily quest should be the most prominent dashboard element. Avoid cluttering every card with glow effects or animation; the interface should motivate action without reducing readability or performance.

### Accessibility and usability

- Provide visible focus states.
- Support keyboard navigation.
- Do not communicate status through color alone.
- Respect reduced-motion preferences.
- Use skeletons or clear loading indicators.
- Explain empty states and recoverable errors.
- Keep daily goal and challenge status understandable without animation.

## 6. Recommended Technology Stack

| Layer | Recommended technology | Responsibility |
|---|---|---|
| Frontend | React + TypeScript | Interactive UI |
| Build tooling | Vite | Development and build |
| Styling | Tailwind CSS | Responsive design system |
| UI components | shadcn/ui | Accessible reusable components |
| Animation | Framer Motion | Limited interface transitions |
| Charts | Recharts | Progress and analytics |
| Backend | Django + Django REST Framework | API and business logic |
| Database | PostgreSQL | Durable relational data |
| Background jobs | Celery + Redis | Scheduled and asynchronous tasks |
| Scheduler | Celery Beat | Periodic challenge generation |
| Backend tests | Django Test Framework or pytest | Business logic and API testing |
| Frontend tests | Vitest and React Testing Library | UI and component testing |
| End-to-end tests | Playwright | Full user journeys |
| Deployment | Docker-based deployment | Repeatable environments |
| Source control | Git + GitHub | Version control and CI |

Start with a modular Django application rather than microservices. Redis and Celery are useful for scheduled jobs and notifications, but do not add Kubernetes until traffic, operational requirements, and cost justify it.

## 7. High-Level Architecture

### Synchronous request flow

`React Frontend → Django REST API → PostgreSQL`

### Background task flow

`Celery Beat → Celery Worker → PostgreSQL`

Optional notifications can be sent through a configured email or push provider.

### Component responsibilities

**Frontend**
- Render dashboard, challenge, pattern, history, and achievement views.
- Submit user actions to the API.
- Display server-returned progress and reward states.

**Backend**
- Authenticate and authorize requests.
- Assign daily questions.
- Validate completion events.
- Calculate goal status and streaks.
- Issue XP and unlock achievements.
- Provide analytics data.

**Database**
- Store users, questions, patterns, challenges, assignments, activity, progress, XP transactions, and achievements.

**Background workers**
- Pre-generate daily challenges.
- Send optional reminders.
- Validate catalog metadata.
- Generate periodic summaries.

## 8. Database Design

Recommended core models:

### User/Profile
Use Django’s authentication model and a profile or custom user model as appropriate. Store display preferences, challenge mode, and timezone. Do not store passwords manually.

### Question
Fields: `id`, `title`, `slug`, `leetcode_url`, `difficulty`, `is_active`, `estimated_minutes`, and catalog metadata.

### Pattern
Fields: `id`, `name`, `slug`, `description`, and ordering metadata.

### QuestionPattern
Many-to-many relationship between questions and patterns. Optionally mark one pattern as primary.

### DailyChallenge
Fields: `id`, `user_id`, `challenge_date`, `status`, and timestamps.

**Constraint:** unique `(user_id, challenge_date)`.

### DailyChallengeQuestion
Fields: `id`, `daily_challenge_id`, `question_id`, `position`, `is_bonus`, and `status`.

Prevent duplicate question assignments within a challenge unless the data model explicitly represents a revision task.

### UserQuestionProgress
Fields: `id`, `user_id`, `question_id`, `status`, `first_attempt_at`, `solved_at`, `solve_count` (only if supported), and `personal_notes`.

Separate overall question progress from challenge assignment so a problem can be revised without corrupting historical challenge records.

### DailyActivity
Fields: `id`, `user_id`, `activity_date`, `questions_completed`, `goal_completed`, `xp_earned`, and `streak_qualified`.

**Constraint:** unique `(user_id, activity_date)`.

### Achievement
Fields: `id`, `name`, `slug`, `description`, `criteria_type`, `criteria_value`, and `is_active`.

### UserAchievement
Fields: `id`, `user_id`, `achievement_id`, and `unlocked_at`.

**Constraint:** unique `(user_id, achievement_id)`.

### XPTransaction
Fields: `id`, `user_id`, `event_type`, `reference_type`, `reference_id`, `xp_amount`, `idempotency_key`, and `created_at`.

Use unique/idempotency constraints to prevent duplicate rewards. Treat the transaction ledger as the audit trail.

### UserPatternProgress
Fields: `id`, `user_id`, `pattern_id`, derived counters, `last_practiced_at`, and optional derived mastery data.

Derived values should be recalculable from source activity. Avoid making cached counters the only source of truth.

## 9. Daily Challenge Generation Logic

1. Load the user’s challenge mode, timezone, completed questions, recent assignments, pattern progress, and due revisions.
2. Filter to active catalog questions matching the selected mode.
3. Exclude previously completed or recently assigned questions unless revision is intentional.
4. Choose a balanced pattern mix and difficulty distribution.
5. Use a deterministic fallback when the eligible catalog is too small.
6. Create the challenge and assignments in a database transaction.
7. Enforce the unique daily challenge constraint so concurrent jobs cannot create duplicates.
8. Return the saved challenge to the frontend.

### Reliability requirements

Use both:
- Scheduled background generation; and
- An idempotent API fallback when the user opens the dashboard and no challenge exists for the current local date.

The fallback must not create duplicate challenges or award rewards. Challenge dates must be calculated from the user’s configured timezone, not assumed to be the server’s local date.

Start with rule-based selection. Machine-learning recommendations are unnecessary until meaningful interaction data exists.

## 10. LeetCode Integration Plan

### Level 1 — MVP: Official links and self-reported completion

- Curate problem metadata and official URLs.
- Open problems on LeetCode in a new tab.
- Let the user record completion in DSA Quest.
- Track streaks, XP, patterns, and history from the app’s own records.
- Clearly label completion as user-reported.

### Level 2 — Supported synchronization

Only implement this after confirming that a reliable and permitted integration is available. Validate terms, authentication, rate limits, data availability, and operational reliability. If supported, synchronize accepted submissions with duplicate-event protection.

### Level 3 — Integrated coding environment

Running code inside DSA Quest would require a separate execution service, sandbox isolation, resource limits, abuse protection, and security review. This is out of scope for the MVP.

Do not build the product around an undocumented endpoint without a fallback plan.

## 11. REST API Plan

Base path: `/api/`

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/auth/register/` | Register a user |
| `POST` | `/auth/login/` | Log in |
| `POST` | `/auth/logout/` | Log out |
| `GET` | `/dashboard/` | Dashboard summary |
| `GET` | `/challenges/today/` | Retrieve today’s challenge |
| `POST` | `/challenges/generate/` | Idempotently create/retrieve today’s challenge |
| `GET` | `/questions/` | Filterable question catalog |
| `GET` | `/questions/{id}/` | Question details |
| `POST` | `/questions/{id}/complete/` | Record completion |
| `GET` | `/progress/` | Progress overview |
| `GET` | `/progress/history/` | Activity history |
| `GET` | `/patterns/` | Pattern catalog and progress |
| `GET` | `/patterns/{id}/` | Pattern detail |
| `GET` | `/achievements/` | Achievement list and unlock status |
| `GET` | `/streak/` | Streak summary |
| `GET` | `/xp/history/` | XP transaction history |

All user-specific reads and writes must be scoped to the authenticated user. Validate request payloads and return consistent error responses.

### Completion endpoint transaction

On a completion request, the backend should:

1. Authenticate the user and validate the assigned question.
2. Check whether the event has already been processed.
3. Update progress and the relevant assignment.
4. Calculate eligible XP server-side.
5. Recalculate daily-goal status.
6. Update streak qualification.
7. Evaluate achievement conditions.
8. Commit related writes atomically.
9. Return the updated challenge, progress, and reward summary.

A retry must not award XP twice. Use database transactions, unique constraints, and idempotency keys where appropriate.

## 12. Security, Reliability, and Operations

### Security
- Use Django’s password and session/authentication mechanisms.
- Apply CSRF protection where relevant.
- Rate-limit authentication and sensitive endpoints.
- Enforce object-level authorization on user-owned records.
- Validate URLs and inputs.
- Keep secrets in environment variables or a secret manager.
- Never commit `.env` files or credentials.
- Use HTTPS in production.

### Reliability
- Structured logs and error tracking.
- Database backups and a tested restore process.
- Health checks for the API, database, and workers.
- Automated tests in CI.
- Database constraints for uniqueness and data integrity.
- Monitoring for failed challenge generation and task retries.
- Clear operational alerts for persistent failures.

### Time and date handling
- Store timestamps in UTC.
- Calculate daily activity dates using the user’s configured timezone.
- Test daylight-saving transitions even if the initial user base is expected to be in India.
- Define how timezone changes affect future streak calculations.
- Never silently rewrite historical activity.

## 13. Testing Strategy

### Backend unit and integration tests
- Registration, login, logout, and authorization.
- Daily challenge generation and duplicate prevention.
- Difficulty-mode selection.
- Empty and insufficient question-catalog fallback.
- Completion and duplicate request handling.
- XP ledger idempotency.
- Daily-goal qualification.
- Streak continuation and reset.
- Timezone boundaries and date changes.
- Achievement unlock conditions.
- Revision assignment behavior.
- API validation and error handling.

### Frontend tests
- Dashboard loading, empty, and error states.
- Challenge rendering and completion.
- XP and streak refresh.
- Achievement states.
- Pattern progress charts.
- Responsive navigation.
- Keyboard and reduced-motion behavior.

### End-to-end acceptance journey

`Register → Login → Open Dashboard → Complete Question 1 → Complete Question 2 → Daily Goal Completed → XP Updated → Streak Updated → Achievement Evaluated → History Updated`

Automate this flow with a browser testing tool such as Playwright.

## 14. Delivery Roadmap

Estimated duration: **6–8 weeks for one developer**, assuming controlled scope and a curated catalog. This is a planning estimate, not a guarantee.

| Week | Deliverables |
|---|---|
| 1 | Requirements, wireframes, schema, repository, local environment |
| 2 | Authentication, question catalog, patterns, seed data |
| 3 | Daily challenge assignment and selection rules |
| 4 | Completion tracking, XP ledger, daily goal, streak logic |
| 5 | Dashboard, history, charts, pattern progress |
| 6 | Achievements, responsive UI, accessibility and motion polish |
| 7 | Automated tests, security review, bug fixes, Docker and deployment |
| 8 | Pilot testing, telemetry review, usability improvements, release |

### Milestone acceptance criteria

**Milestone 1 — Foundation**
- User can register and sign in.
- Database migrations run cleanly.
- Question catalog and pattern relationships are available.

**Milestone 2 — Daily practice**
- Exactly one challenge can exist per user-local date.
- Two mandatory questions are assigned where catalog supply permits.
- Challenge generation is safe to retry.

**Milestone 3 — Rewards**
- Completion updates progress.
- XP cannot be duplicated by retrying requests.
- Streak and daily-goal rules pass automated tests.

**Milestone 4 — Dashboard**
- Dashboard reflects backend data.
- History, patterns, and achievements are navigable.
- Responsive and accessible states are implemented.

**Milestone 5 — Release readiness**
- Core end-to-end flow passes.
- Secrets are excluded from version control.
- Production configuration, backups, logging, and health checks are documented.

## 15. Success Metrics

Initial targets below are hypotheses to validate, not industry benchmarks.

| Metric | Definition | Initial target |
|---|---|---:|
| Daily goal completion rate | Active users completing both daily questions | 60%+ |
| D7 retention | Users returning seven days after activation | 25%+ |
| D30 retention | Users returning thirty days after activation | 10%+ |
| Challenge generation failure rate | Failed challenge generations / generation attempts | <1% |
| Duplicate XP transactions | Duplicate reward events successfully credited | 0 |
| Pattern coverage | Distinct patterns practiced per active user | Track baseline |
| Revision completion rate | Due revision tasks completed | Track baseline |
| Verified solve rate | Accepted submissions / verified attempts, if integration supports it | Establish baseline |

Measure learning outcomes as well as engagement. High streak counts do not prove that users are improving. Once trustworthy attempt data exists, review correctness, revision performance, and progression into harder problems.

## 16. Proposed Repository Structure

```text
dsa-quest/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── layouts/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   ├── utils/
│   │   └── features/
│   │       ├── dashboard/
│   │       ├── challenges/
│   │       ├── questions/
│   │       ├── patterns/
│   │       ├── achievements/
│   │       └── progress/
│   └── package.json
├── backend/
│   ├── config/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── questions/
│   │   ├── challenges/
│   │   ├── progress/
│   │   ├── gamification/
│   │   └── analytics/
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database-schema.md
│   └── api-specification.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

This is a starting point. Keep app boundaries aligned with actual domain responsibilities and avoid unnecessary abstractions.

## 17. Key Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Unreliable or unavailable LeetCode submission integration | Automatic progress sync may fail | Launch with official links and self-reported completion; keep sync optional |
| Users game XP | Progress and rewards become untrustworthy | Server-side validation, idempotency, auditable XP ledger |
| Streak pressure discourages returning users | Drop-off after a missed day | Clear rules, supportive recovery messaging, defer streak freeze until validated |
| Question catalog is too small | Repetition and poor challenge quality | Curate and validate a sufficiently broad catalog; implement deterministic fallback |
| Timezone bugs | Incorrect streaks and daily assignments | Store UTC timestamps, calculate local dates explicitly, test boundaries |
| Gamification hides weak learning outcomes | Users remain engaged without improving | Track revision, pattern coverage, and verified correctness when available |
| Premature infrastructure complexity | Higher cost and slower delivery | Start with a modular monolith and scale only from measured need |

## 18. Immediate Next Steps

Execute in this order:

1. Finalize the MVP scope and daily-goal rules.
2. Create low-fidelity wireframes for the dashboard, daily challenge, pattern page, and history.
3. Define Django models and database constraints.
4. Seed a small, verified LeetCode question catalog across the initial patterns.
5. Implement authentication and the question catalog API.
6. Build idempotent daily challenge generation.
7. Implement completion, XP, goal, streak, and achievement transactions.
8. Connect the React dashboard to live API data.
9. Add automated tests for duplicate events and timezone boundaries.
10. Deploy a small pilot and measure whether users return and improve.

## 19. Final Product Principle

Build the smallest reliable product that makes daily DSA practice easier to start and easier to sustain.

The differentiator is not badges or animation by themselves. It is the combination of **daily challenges, pattern-based progression, meaningful revision, trustworthy history, and clear feedback**. Ship that loop first; add AI recommendations, leaderboards, and advanced analytics only when usage data demonstrates a need.
