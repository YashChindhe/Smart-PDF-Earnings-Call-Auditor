FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for database compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend subdirectory
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from backend subdirectory to container root
COPY backend/ .

EXPOSE 7860

# Run uvicorn on dynamic port provided by Railway, default to 7860
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-7860}"]
