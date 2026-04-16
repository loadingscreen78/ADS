# Drift Monitor Service
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY data/ ./data/

# Expose port
EXPOSE 8001

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV DRIFT_CHECK_INTERVAL=300

# Run drift monitor
CMD ["python", "-m", "src.services.drift_monitor"]
