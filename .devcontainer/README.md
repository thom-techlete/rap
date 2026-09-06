# RAP devcontainer

The devcontainer provides Python 3.12, uv, PostgreSQL, and Redis. Dependencies
are installed from the committed `uv.lock` file into `/workspaces/rap/.venv`.

After opening the repository in the container, the Django development server,
Celery worker, and Celery beat start automatically. Their logs are written to
`logs/`.

Manage them with:

```bash
bash .devcontainer/dev-services.sh status
bash .devcontainer/dev-services.sh restart
bash .devcontainer/dev-services.sh stop
```

Run migrations or start Django manually when needed:

```bash
uv run python web/manage.py migrate
uv run python web/manage.py runserver 0.0.0.0:8000
```

The database and Redis services are available as `db` and `redis`.
