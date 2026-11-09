# NeuroQuest CLI image (ADR-019, ADR-021). Secrets are read at runtime, never baked in.
# Use scripts/start.sh and scripts/stop.sh, or one-off:
#   docker run --rm -it -w /repo -v "$PWD":/repo:ro -v neuroquest-var:/var/lib/neuroquest neuroquest review A G N
# (-w /repo lets the app read /repo/.env; docker --env-file keeps quotes and breaks NEUROQUEST_MODEL_PRICES.)
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" \
    NEUROQUEST_REPO_ROOT=/repo \
    NEUROQUEST_STATE_DIR=/var/lib/neuroquest

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
RUN uv sync --frozen --no-dev \
    && useradd --create-home --uid 10001 neuroquest \
    && mkdir -p /var/lib/neuroquest \
    && chown neuroquest /var/lib/neuroquest

USER neuroquest
VOLUME ["/var/lib/neuroquest"]
ENTRYPOINT ["neuroquest"]
CMD ["--help"]
