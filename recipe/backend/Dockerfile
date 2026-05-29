# Recipe Box API — production image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencies first for better layer caching. recipe-scrapers pulls lxml, which
# ships manylinux wheels, so no system build toolchain is required.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Render injects $PORT; default 8000 for plain `docker run`.
ENV PORT=8000
EXPOSE 8000

# Gunicorn with Uvicorn workers. Generous timeout so the LLM / URL-fetch calls in
# /api/recipes/parse can complete. Migrations are run separately (see render.yaml
# preDeployCommand or docker-compose `migrate`), not on every worker boot.
CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w ${WEB_CONCURRENCY:-2} -b 0.0.0.0:${PORT} --timeout 120 --access-logfile -"]
