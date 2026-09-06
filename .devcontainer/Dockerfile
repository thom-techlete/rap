FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG USERNAME=vscode
ARG UV_VERSION=0.11.7

ADD https://astral.sh/uv/${UV_VERSION}/install.sh /tmp/uv-installer.sh

RUN env UV_UNMANAGED_INSTALL="/usr/local/bin" sh /tmp/uv-installer.sh \
    && rm /tmp/uv-installer.sh \
    && rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libpq-dev \
        netcat-openbsd \
        postgresql-client \
        redis-tools \
        bubblewrap \
        socat \
    && rm -rf /var/lib/apt/lists/*

# Install 1Password CLI for the standard Techletes development environment.
RUN curl -sS https://downloads.1password.com/linux/keys/1password.asc \
    | gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" \
    | tee /etc/apt/sources.list.d/1password.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends 1password-cli \
    && rm -rf /var/lib/apt/lists/*

RUN su - "${USERNAME}" -c 'curl -fsSL https://bun.sh/install | bash'

# Codex CLI ships as an npm package and requires Node.js 22+.
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @openai/codex \
    && codex --version \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BUN_INSTALL="/home/${USERNAME}/.bun" \
    PATH="/home/${USERNAME}/.bun/bin:${PATH}" \
    PYTHONPATH=/workspaces/rap/web \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/workspaces/rap/.venv \
    UV_PYTHON_DOWNLOADS=never

RUN mkdir -p /home/vscode/.cache/uv /home/vscode/.cache/pre-commit \
    && chown -R vscode:vscode /home/vscode/.cache
