FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

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

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY . .

# Drop root: run as an unprivileged user. The app writes nothing under /app in
# prod (uploads go to GCS), and 8000 is a non-privileged port, so no extra caps
# are needed. chown lets local-dev (BLOB_STORE=local writing var/uploads) work.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
