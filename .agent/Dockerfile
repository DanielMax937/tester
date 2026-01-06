FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock* requirements.txt* ./
RUN if [ -f uv.lock ]; then uv sync --frozen --system; else uv pip install --system -r requirements.txt; fi
COPY . .
CMD ["python", "app.py"]
