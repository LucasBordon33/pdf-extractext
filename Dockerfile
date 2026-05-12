FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY . .

RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runner

WORKDIR /app

# 1. Traemos el entorno virtual ya hecho desde el builder
COPY --from=builder /app/.venv /app/.venv

# 2. Copiamos el código fuente de nuestra PC al runner
# (Nuevamente, el .dockerignore evita que se copie basura)
COPY . .

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
