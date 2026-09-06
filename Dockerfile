# Use Python 3.12 slim image
FROM python:3.12-slim

# Pin the dependency installer independently from the application dependencies.
ARG UV_VERSION=0.11.7

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=rap_web.settings
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH="/app"

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

# Install Python dependencies from the committed lockfile.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Copy entrypoint script
COPY docker/entrypoint.sh /entrypoint.sh

# Copy project
COPY web/ .

# Create static files directory and logs
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Create a non-root user
RUN groupadd -r django && useradd -r -g django django
RUN chown -R django:django /app
RUN chmod +x /entrypoint.sh
USER django

# Expose port
EXPOSE 8000

# Set entrypoint and default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn"]
