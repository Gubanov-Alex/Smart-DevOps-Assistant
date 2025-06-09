FROM python:3.12-slim AS base


RUN apt-get update && apt-get install -y \
    curl build-essential libpq-dev \
    && pip install --no-cache-dir poetry==1.8.3 \
    && poetry config virtualenvs.create false \
    && poetry config cache-dir /opt/poetry-cache \
    && poetry config installer.parallel true \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY pyproject.toml poetry.lock ./


FROM base AS production
RUN --mount=type=cache,target=/opt/poetry-cache \
    poetry install --only main --no-root --no-dev

COPY . .
RUN mkdir -p models
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM production AS development
RUN --mount=type=cache,target=/opt/poetry-cache \
    poetry install --with dev --no-root
    
