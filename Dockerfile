# NeuroQuest CLI image (ADR-019, ADR-021). Secrets are passed at runtime, never baked in:
#   docker build -t neuroquest .
#   docker run --rm -it --env-file .env -v "$PWD":/repo:ro -v neuroquest-var:/var/lib/neuroquest neuroquest review A G N
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
