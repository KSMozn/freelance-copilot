FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential libpq-dev curl \
       # WeasyPrint runtime: cairo / pango / gdk-pixbuf / harfbuzz / libffi
       # for the student CV PDF renderer. Without these the slim image
       # raises ImportError at first /students/cv.pdf call.
       libcairo2 libpango-1.0-0 libpangoft2-1.0-0 \
       libgdk-pixbuf-2.0-0 libharfbuzz0b libffi-dev shared-mime-info fonts-dejavu \
    && rm -rf /var/lib/apt/lists/*

# uv installs exactly what uv.lock pins, so the image can never drift from the
# dependency set CI verified. The venv lives OUTSIDE /app because dev compose
# bind-mounts ./backend over /app (a venv under /app would be shadowed away).
COPY --from=ghcr.io/astral-sh/uv:0.10 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_COMPILE_BYTECODE=1 \
    UV_NO_CACHE=1 \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dev --no-install-project

COPY . .
RUN uv sync --frozen --extra dev

# Drop root: run as an unprivileged user. The app writes nothing under /app in
# prod (uploads go to GCS), and 8000 is a non-privileged port, so no extra caps
# are needed. chown lets local-dev (BLOB_STORE=local writing var/uploads) work.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
