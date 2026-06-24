#Step 1 - Version
FROM python:3.13-slim

#Step 2 - ENVS (normally optional but Python is weird)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_PREFERENCE=only-system

#Step 3 - copy the uv binary from the official image (normally we would do uv install )
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

#Step 4 - setup the working directory
WORKDIR /app

#Step 5 - copy the dependencies
COPY pyproject.toml uv.lock ./

#Step 6 - freeze the dependencies into a virtual environment
RUN uv sync --frozen --no-dev

#Step 7 - set the path to the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

#Step 8 - copy the application code
COPY app/ ./app/

#Step 9 - copy the migrations and alembic config
COPY migrations/ ./migrations/

COPY alembic.ini ./

#Step 10 - create a user with least privileges and change ownership of the application directory
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

#Step 11 - run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]