FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y fluidsynth git wget curl ffmpeg libsndfile1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN git clone https://github.com/misya11p/amt-apc.git /app/amt-apc

RUN mkdir -p /app/amt-apc/models/params && \
    wget -P /app/amt-apc/models/params/ https://github.com/misya11p/amt-apc/releases/download/beta/apc.pth

COPY amtworkers/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && \
    apt-get install -y curl && \
    curl -L -o FluidR3_GM.sf3 "https://github.com/musescore/MuseScore/raw/master/share/sound/FluidR3Mono_GM.sf3" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY amtworkers/ ./amtworkers
COPY packages/ ./packages
COPY uploads/ ./uploads

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development \
    PYTHONPATH=/app

ENTRYPOINT []
CMD ["python", "-u", "amtworkers/worker.py"]