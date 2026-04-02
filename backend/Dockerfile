FROM python:3.13-slim

WORKDIR /app

# Install uv for faster installs
RUN pip install uv

# Copy dependency spec first for layer caching
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system -r pyproject.toml

# Copy source
COPY backend/ ./backend/

# Expose port
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
