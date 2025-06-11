FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Update CA certificates
RUN update-ca-certificates

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Demucs models during build (saves startup time)
RUN python -c "from demucs.pretrained import get_model; get_model('htdemucs')"

# Install Basic Pitch and download its models
RUN pip install basic-pitch
RUN python -c "from basic_pitch import ICASSP_2022_MODEL_PATH; import basic_pitch.inference"

# Copy YourMT3 repository (if using it)
COPY YourMT3/ ./YourMT3/
RUN cd YourMT3 && pip install -e .

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /tmp/audio_processing
RUN mkdir -p /app/uploads

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import redis; r=redis.from_url('${REDIS_URL}'); r.ping()" || exit 1

# Run the worker
CMD ["python", "-m", "workers"]