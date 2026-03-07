FROM python:3.13-bookworm

# Install system dependencies: Node.js (for mystmd), PostgreSQL client, Docker CLI, and misc tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    nano \
    procps \
    less \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" \
        > /etc/apt/sources.list.d/pgdg.list' \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor \
        -o /etc/apt/trusted.gpg.d/postgresql.gpg \
    && apt-get update \
    && apt-get install -y postgresql-client-16 \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor \
        -o /etc/apt/keyrings/docker.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian bookworm stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (early for layer caching)
COPY requirements.workspace.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.workspace.txt \
    && python -m bash_kernel.install

# Install mystmd globally via npm
RUN npm install -g mystmd

# pgdb: run a shell command inside the db container (for OS-level inspection of the PG cluster)
RUN printf '#!/bin/sh\ndocker exec -u postgres "${DB_CONTAINER:-db}" bash -c "$*"\n' \
    > /usr/local/bin/pgdb \
    && chmod +x /usr/local/bin/pgdb

# Copy pgpass for passwordless psql connections to the db service
COPY --chown=root:root --chmod=600 pg-files/.pgpass /root/.pgpass

WORKDIR /workspace

# Default: keep the container alive for docker compose / dev container use
CMD ["tail", "-f", "/dev/null"]
