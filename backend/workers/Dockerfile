FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Update CA certificates
RUN update-ca-certificates

# Pre-download Demucs models during build
RUN pip install demucs torch torchaudio
RUN python -c "from demucs.pretrained import get_model; get_model('htdemucs')"

# ... rest of your Dockerfile