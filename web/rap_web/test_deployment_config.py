from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_production_compose_uses_compose_service_hosts():
    compose = (REPOSITORY_ROOT / "docker/docker-compose.yml").read_text()

    assert "POSTGRES_HOST: db" in compose
    assert "REDIS_URL: redis://redis:6379/0" in compose


def test_deployment_preserves_server_owned_environment_file():
    workflow = (REPOSITORY_ROOT / ".github/workflows/ci-cd.yml").read_text()

    assert "production_env_backup" in workflow
    assert 'cp "$production_env_backup" .env' in workflow


def test_application_drops_privileges_after_reading_startup_secrets():
    dockerfile = (REPOSITORY_ROOT / "Dockerfile").read_text()
    entrypoint = (REPOSITORY_ROOT / "docker/entrypoint.sh").read_text()

    assert "apt-get install" in dockerfile and "gosu" in dockerfile
    assert 'exec gosu django "$@"' in entrypoint
