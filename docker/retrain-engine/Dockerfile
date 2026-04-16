# Retrain Engine Service
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY data/ ./data/

# Expose port
EXPOSE 8002

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_DIR=/app/data/models
ENV USE_GPU=false

# Run retrain engine
CMD ["python", "-m", "src.services.retrain_service"]
