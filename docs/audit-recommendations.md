# RAP audit recommendations

Date: 2026-09-06  
Scope: repository source, Django configuration, Docker/Compose, CI/CD, scripts,
dependencies, and documentation. This is a source-level audit; it does not prove
the state of the deployed VPS or production traffic.

## Executive summary

The project has a usable Django foundation and the focused test suite passes, but
it should not be treated as production-ready until the first six findings below
are addressed. The most important risks are:

1. Secret-like configuration and a private-key marker are committed to Git.
2. The locked dependency set has 140 known vulnerability records across 12
   packages.
3. Production settings have insecure fallbacks, and the generated random admin
   URL is not connected to the actual URL route.
4. Rate limiting is not clearly shared across Gunicorn workers, trusts forwarded
   client IP data, and Axes reports a bypass-prone username-only configuration.
5. Authenticated state-changing push endpoints explicitly disable CSRF checks.
6. Analytics and several list/admin pages perform unbounded or N+1 query work.

The project is small enough that a focused hardening pass should be preferred to
a rewrite. The current codebase does not need a new architecture before these
boundary, integrity, and query-shape issues are fixed.

## Prioritized recommendations

### P0 - address before the next production deployment

#### 1. Revoke and remove committed secrets

Evidence:

- `.env` and `docker/.env` are tracked files. The local scan classified both as
  containing non-default secret-like configuration, including a database URL.
- `docs/PWA_IMPLEMENTATION.md` contains lines flagged as private-key material by
  `detect-secrets`.
- `.secrets.baseline` is empty, while secret scanning is commented out in
  `.pre-commit-config.yaml`.

Recommendation:

- Treat every credential/key in Git history as exposed: rotate the Django key,
  database credentials, email credentials, Redis credentials if applicable, and
  VAPID private key.
- Remove `.env`, `docker/.env`, and private-key material from the repository and
  clean history according to the repository retention policy.
- Store runtime secrets only in the deployment secret store or protected CI
  environment. Keep a redacted `.env.example` with no working credentials.
- Re-enable `detect-secrets` in CI and fail on new unreviewed findings. Keep the
  baseline small and reviewed rather than using it as a blanket allowlist.

Verification: scan tracked files and Git history after rotation; confirm the
application starts with secrets supplied externally and fails without required
production secrets.

#### 2. Patch and continuously gate dependencies

Evidence: `uv tool run pip-audit -r requirements.txt` found 140 vulnerability
records across 12 packages, including Django 5.2.5, aiohttp 3.12.15,
cryptography 45.0.6, Django REST Framework 3.16.1, Pillow 11.3.0, requests,
urllib3, sqlparse, and setuptools. The exact advisory set is time-sensitive and
should be refreshed when remediation starts.

Recommendation:

- Update the direct dependencies in `pyproject.toml` first, then regenerate both
  hashed lockfiles with the project’s pip-tools workflow.
- Prioritize Django, Pillow, cryptography, aiohttp, sqlparse, requests/urllib3,
  and DRF; confirm compatibility with Celery and pywebpush.
- Run the audit in CI against the lockfile and fail on unfixed high/critical
  issues, with an explicit reviewed exception process for anything deferred.

Verification: `pip-audit -r requirements.txt`, Django tests, migrations check,
Docker build, and a smoke test of login, uploads, notifications, and password
reset.

#### 3. Make production configuration fail closed

Evidence:

- `web/rap_web/settings.py:55-57` falls back to a known Django secret.
- `web/rap_web/settings.py:160-168` falls back to a known database password.
- `web/rap_web/settings.py:326-340` allows HTTPS redirect and secure cookies to
  be disabled by omission or a wrong environment value.
- `scripts/generate_secrets.sh:76-77` generates `ADMIN_URL`, but
  `web/rap_web/urls.py:26-35` always registers `path("admin/", ...)`.
  Therefore the advertised randomized admin URL does not protect the admin.
- `docker/caddy/Caddyfile.prod:7` is hard-coded to `rap8.nl` and `www.rap8.nl`,
  while the deployment scripts accept an arbitrary domain argument.

Recommendation:

- Separate development and production settings, or enforce a production mode
  that raises on missing `DJANGO_SECRET_KEY`, database password, allowed hosts,
  and required email/Redis configuration.
- Reject `DEBUG=True`, wildcard hosts, insecure cookies, and disabled HTTPS in a
  production startup check rather than merely emitting Django warnings.
- Wire `ADMIN_URL` into the URL configuration, or remove the claim that the admin
  URL is randomized and protect `/admin/` through a real access-control measure.
- Template the Caddy site name from the same validated deployment domain, or
  support only the one hard-coded domain and reject other arguments.

Verification: run `manage.py check --deploy` with a production-like environment
and make missing/unsafe values fail the process; test the effective admin route
and HTTPS redirect through Caddy.

### P1 - address next

#### 4. Repair CSRF, proxy identity, and rate-limit semantics

Evidence:

- `web/notifications/views.py:130-131`, `176-177`, and `209-212` disable CSRF
  for authenticated state-changing endpoints.
- There is no `CACHES` configuration in `settings.py`; Django therefore uses its
  default local-memory cache unless another environment override exists. The
  custom limiter in `security_middleware.py:117-175` is consequently not a
  reliable shared limit across Gunicorn workers.
- `security_middleware.py:100-107` and `179-186` take the first
  `X-Forwarded-For` value without proving that the request came through a
  trusted proxy.
- Django’s check reported `axes.W006`: `AXES_LOCKOUT_PARAMETERS` is only
  `['username']` in `settings.py:410-418`, allowing attackers to rotate other
  request dimensions and bypass IP-based protection.

Recommendation:

- Remove `csrf_exempt` and use the existing CSRF cookie/header flow for push
  subscription and test-notification requests. If a separate API is required,
  define an explicit token/origin contract instead of exempting the view.
- Configure Redis as Django’s shared cache with a dedicated key prefix and test
  rate limits through two web workers.
- Configure the actual proxy chain and derive client IP only from trusted proxy
  headers; otherwise use the socket peer address.
- Choose a documented lockout policy that balances account lockout abuse against
  credential-stuffing resistance, then test it with multiple IPs and usernames.

Verification: cross-worker rate-limit test, forged `X-Forwarded-For` test,
CSRF-negative tests for every state-changing endpoint, and an Axes deployment
check with the production middleware enabled.

#### 5. Split public liveness from internal readiness

Evidence: `web/rap_web/middleware.py:23-34` makes `health_check` public, while
`web/rap_web/health.py:29-119` performs database, cache, Celery inspection, and
SMTP connection checks. The response includes database engine/name, worker
names, email host, debug mode, filesystem paths, and raw exception strings.

This is both a performance problem (a health request can block on several
backends) and an information-disclosure problem.

Recommendation:

- Make public liveness a cheap process check with no infrastructure details.
- Keep readiness checks internal or authenticated and use short timeouts.
- Do not open an SMTP connection or call Celery `Inspect` on every probe; use
  separate probes or cached background status.
- Return generic component status externally and log detailed failures only on
  the server side.

Verification: measure `/health/` under repeated probes and confirm no secrets,
paths, exception text, worker names, or backend hostnames are exposed.

#### 6. Enforce upload validation at the content boundary

Evidence:

- `web/users/forms.py:18-66` treats `python-magic` as optional. In this project it
  is not declared in `requirements.txt`, so validation can fall back to the
  client-provided `content_type` and extension.
- The broad exception handler at `forms.py:44-53` can turn a failed magic check
  into a permissive fallback.
- Uploaded files are stored through `Player.foto` at
  `web/users/models.py:136-141` and publicly served under `/media/` by Caddy.

Recommendation:

- Validate with Pillow server-side (`verify`, pixel/decompression limits), then
  re-encode to a safe format and discard the original bytes.
- Enforce size, dimensions, extension, and content-type limits independently of
  browser metadata; make the validator dependency explicit if libmagic remains
  necessary.
- Use generated filenames and consider private media or an attachment response
  with a safe content disposition.
- Add regression tests for polyglot files, invalid images, oversized images, and
  decompression-bomb behavior.

#### 7. Fix registration and attendance races with database constraints

Evidence:

- Invitation validation occurs in `web/users/forms.py:283-300`, then the user and
  usage count are saved separately at `forms.py:302-317`.
- `InvitationCode.use_code()` only increments an in-memory value at
  `web/users/models.py:96-99`; concurrent registrations can exceed `max_uses`.
- `web/attendance/models.py:7-11` has no uniqueness constraint, while
  `web/attendance/views.py:20`, `118`, and `150` use `get_or_create`. Concurrent
  requests can create duplicate attendance rows.

Recommendation:

- Add `UniqueConstraint(fields=["user", "event"])` for attendance and migrate
  existing duplicates before enabling it.
- Wrap invitation consumption in `transaction.atomic()`, lock the invitation
  row, and update only when it is still active, unexpired, and below its limit.
- Add concurrency tests for both paths; do not rely on form validation for an
  invariant that belongs in the database.

#### 8. Remove unbounded and N+1 query paths

Evidence:

- `web/events/analytics_views.py:41-191` performs repeated count queries for
  months, event types, and weekdays.
- `analytics_views.py:314-325` loops through events and then attendance rows in
  Python; `360-440` loops over every active player and queries attendance for
  each player.
- `web/users/views.py:291-307` performs two attendance counts per admin event
  while iterating an unbounded queryset.
- `web/polls/models.py:94-108` counts votes once per option, an N+1 pattern.
- Event list/admin pages do not paginate their primary querysets.

Recommendation:

- Replace loops with `annotate`, conditional `Count`, grouped aggregates, and
  bounded date ranges.
- Add pagination to event, player, poll, notification, and admin lists.
- Add indexes based on measured query plans, starting with event date/type,
  attendance `(event, user)` and `(event, present)`, and match-statistic lookup
  fields.
- Cache or asynchronously materialize the analytics dashboard if it is used
  regularly; do not cache user-specific results globally.
- Add query-count tests for the analytics, admin event, poll results, and event
  detail views.

### P2 - structural and operational improvements

#### 9. Establish one configuration and security source of truth

Evidence:

- `web/rap_web/security.py` duplicates settings, but `settings.py` defines its
  own values and does not import that module. Its CSP, CORS, database SSL, and
  `SESSION_SAVE_EVERY_REQUEST` settings are therefore easy to mistake for active
  configuration.
- The project declares three environment/configuration libraries in
  `pyproject.toml:34-50` (`python-dotenv`, `django-environ`, and
  `python-decouple`).
- `pyproject.toml:6-9`, `73-98` still describes a `python-basic-template` and
  configures coverage for `utils`/`example`, not this Django project.

Recommendation:

- Keep one settings module (with explicit development/test/production overlays
  if needed) and remove dead duplicate security configuration.
- Choose one environment parser and document the precedence rules.
- Rename the package metadata and replace template-era pytest/coverage/package
  discovery settings with Django-specific commands and coverage targets.
- Either remove unused dependencies such as DRF/AnyMail or document and test
  the feature they support.

#### 10. Make CI/CD validate what it deploys

Evidence:

- `.github/workflows/ci-cd.yml` is triggered on merged pull requests rather than
  normal `push` to `main`, and its job name says quality checks while the shown
  steps do not run Ruff, Black, `pip-audit`, or secret scanning.
- Tests use `web/rap_web/test_settings.py`, which replaces PostgreSQL with
  SQLite, uses MD5 password hashing, disables Axes/authentication middleware,
  and disables the custom security middleware.
- The deploy script first deploys the mutable `latest` image and only records a
  commit tag afterward (`ci-cd.yml:295-309`).
- `scripts/deploy.sh:117-126` stops services for a backup, uses a hard-coded
  database name/user, and the CI deploy runs `docker system prune -f`, which can
  remove unrelated unused Docker resources on a shared host.

Recommendation:

- Run quality, dependency, secret, and Django deployment checks on every PR and
  on pushes to the deployment branch; fail on security warnings that are not
  explicitly allowed.
- Keep fast SQLite tests, but add a small PostgreSQL/production-settings suite
  for constraints, migrations, proxy headers, cache/rate limits, uploads, and
  health probes.
- Deploy the immutable `sha-...` image directly, record the exact digest, and
  roll back to that digest. Avoid mutable `latest` in the deployment decision.
- Remove broad host-wide pruning from automated deployment and make backup
  database names/configuration come from the same validated environment.
- Pin third-party GitHub Actions to commit SHAs and reduce workflow token
  permissions per job.

#### 11. Add basic observability and recovery proof

The code has logging and backup commands, but the audit found no evidence in the
repository of a tested restore, query latency budget, error-rate alert, queue
backlog alert, or production smoke test. Add:

- structured request/error logs without credentials or full sensitive form data;
- database, Redis, Celery, and disk alerts;
- a scheduled backup retention policy and a documented restore drill;
- a post-deploy smoke test covering HTTPS, login, an attendance write, static
  files, and health/readiness behavior.

## Suggested execution order

### First 1-2 days

1. Rotate/remove secrets and private keys.
2. Upgrade vulnerable dependencies and regenerate lockfiles.
3. Make production settings fail closed and fix the admin/Caddy domain mismatch.
4. Remove CSRF exemptions and configure shared Redis caching/rate limits.

### Next week

5. Replace the public detailed health check.
6. Add database constraints and transactional invitation consumption.
7. Harden image uploads.
8. Refactor the analytics/admin/poll query paths and add pagination/query-count
   tests.

### After hardening

9. Consolidate settings/dependencies and remove template leftovers.
10. Make CI/CD immutable, security-gated, and restore-tested.

## Verification already performed

- `python manage.py test --settings=rap_web.test_settings --verbosity=1`: **69
  tests passed**.
- `python manage.py makemigrations --check --dry-run
  --settings=rap_web.test_settings`: **no model changes detected**.
- `docker compose -f docker/docker-compose.prod.yml config --quiet`: passed.
- `docker compose -f docker/docker-compose.dev.yml config --quiet`: passed.
- `docker build --check -f Dockerfile .`: passed.
- `uv tool run pip-audit -r requirements.txt`: found **140 vulnerability
  records in 12 packages**.
- Django deployment check emitted **9 warnings** under the local development
  environment, including missing secure cookies/HTTPS, weak fallback secret,
  DEBUG enabled, and the Axes configuration warnings. These warnings are not
  proof of the production environment because the local `.env` is explicitly
  development-oriented.

Not performed: live VPS checks, browser/device performance measurements,
production Lighthouse, real traffic profiling, backup restore, or external
penetration testing.
