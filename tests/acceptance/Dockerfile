ARG BASE_IMAGE=python:3.11-slim-bookworm
FROM ${BASE_IMAGE}
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 POETRY_VIRTUALENVS_IN_PROJECT=true \
    PYTHONUNBUFFERED=1 PYTHONNOUSERSITE=1 LANGFUSE_TRACING_ENABLED=false
RUN apt-get update && apt-get install -y --no-install-recommends git nodejs \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/tooling \
    && /opt/tooling/bin/python -m pip install poetry==2.4.1
WORKDIR /project
COPY pyproject.toml poetry.lock ./
RUN /opt/tooling/bin/poetry install --with dev -E mcp --no-root --no-interaction
COPY . .
RUN /opt/tooling/bin/poetry install --only-root --no-interaction \
    && .venv/bin/python -m pip install 'cryptography>=41,<52' \
    && .venv/bin/python -m pip check \
    && /opt/tooling/bin/poetry build --format wheel --output /opt/wheels/core
RUN set -eu; \
    if [ -d research-input/source ]; then \
        .venv/bin/python -m pip wheel --no-deps ./research-input/source --wheel-dir /opt/wheels/research; \
    elif [ -d research-input/wheel ]; then \
        mkdir -p /opt/wheels/research; \
        cp research-input/wheel/*.whl /opt/wheels/research/; \
    fi
ENV PATH=/project/.venv/bin:/usr/local/bin:/usr/bin:/bin VIRTUAL_ENV=/project/.venv
CMD ["python", "tests/acceptance/verify.py", "--output", "/reports"]
