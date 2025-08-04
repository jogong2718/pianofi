FROM tanchihpin0517/picogen2:latest-full

# replace with requirements.txt when it gets made

COPY workers/requirements.txt /app/requirements.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    conda run -n picogen2 /bin/bash -c "\
    pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt \
    " && \
    conda clean -afy

WORKDIR /app

RUN curl -L "https://github.com/musescore/MuseScore/raw/master/share/sound/FluidR3Mono_GM.sf3" -o FluidR3_GM.sf3

COPY workers/ ./workers
COPY packages/ ./packages
COPY uploads/ ./uploads

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development \
    PYTHONPATH=/app

ENTRYPOINT []
CMD ["/home/picogen2/miniconda/envs/picogen2/bin/python", "-u", "workers/worker.py"]