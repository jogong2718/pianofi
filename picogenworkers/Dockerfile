FROM tanchihpin0517/picogen2:latest-full

COPY picogenworkers/requirements.txt /app/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    conda run -n picogen2 /bin/bash -c "\
    pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt \
    " && \
    conda clean -afy

WORKDIR /app

USER root
RUN apt-get update && \
    apt-get install -y curl && \
    curl -L -o FluidR3_GM.sf3 "https://github.com/musescore/MuseScore/raw/master/share/sound/FluidR3Mono_GM.sf3" && \
    chown picogen2:picogen2 FluidR3_GM.sf3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER picogen2

COPY picogenworkers/ ./picogenworkers
COPY packages/ ./packages
COPY uploads/ ./uploads

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PYTHONPATH=/app

ENTRYPOINT []
CMD ["/home/picogen2/miniconda/envs/picogen2/bin/python", "-u", "picogenworkers/worker.py"]