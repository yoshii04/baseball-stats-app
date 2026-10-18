FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /bin/bash --create-home appuser

# Install Python dependencies
COPY webapp/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
# secrets.json は volume mount で提供するため含めない
COPY webapp/backend/ ./webapp/backend/
COPY config/config.py ./config/config.py
COPY utils/run_logger.py ./utils/run_logger.py

WORKDIR /app/webapp/backend

# Transfer ownership and switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
