FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y fluidsynth git wget curl ffmpeg libsndfile1 lilypond && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ptiworkers/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

RUN apt-get update && \
    apt-get install -y curl && \
    curl -L -o FluidR3_GM.sf3 "https://github.com/musescore/MuseScore/raw/master/share/sound/FluidR3Mono_GM.sf3" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ptiworkers/ ./ptiworkers
COPY packages/ ./packages

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app

ENTRYPOINT []
CMD ["python", "-u", "ptiworkers/worker.py"]
