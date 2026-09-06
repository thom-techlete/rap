# Operations runbook

## Post-deploy smoke test

Run these checks against the deployment host after the immutable image is
started. Do not put credentials in shell history or CI logs.

```bash
curl --fail --silent --show-error https://rap8.nl/health/
curl --fail --silent --show-error https://rap8.nl/static/admin/css/base.css
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs --tail=100 web celery_worker celery_beat
```

The public health response must be exactly a generic healthy status. The
authenticated `/readiness/` endpoint can be checked by an authorized operator
from the internal access path; it must not be exposed as a public proxy probe.

## Backup and restore drill

Create backups outside the repository with restricted permissions and retain
multiple dated copies according to the hosting policy:

```bash
umask 077
docker compose -f docker/docker-compose.yml exec -T db \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "/secure-backups/rap-$(date +%F).sql"
```

At least quarterly, restore a copy into a disposable PostgreSQL instance and
verify migrations plus a read-only login/dashboard smoke test. Never restore a
backup over production as part of the drill. Record the backup date, image
digest, restore duration, and result in the operations log.

## Alerting baseline

The deployment monitor should alert on: failed HTTPS liveness, failed internal
readiness, PostgreSQL/Redis health, Celery worker absence or queue growth, disk
usage, and elevated 5xx responses. Application logs are emitted without form
passwords or secret values; retain and rotate them at the container/host layer.
