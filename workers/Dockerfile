FROM tanchihpin0517/picogen2:latest-full

# replace with requirements.txt when it gets made
RUN --mount=type=cache,target=/root/.cache/pip \
    conda run -n picogen2 /bin/bash -c "\
    pip install --upgrade pip && \
    pip install --no-cache-dir \
    redis \
    rq \
    boto3 \
    sqlalchemy \
    " && \
    conda clean -afy

ARG UID=10001
ARG USERNAME=appuser
RUN useradd -m -u ${UID} ${USERNAME}
USER ${USERNAME}

WORKDIR /app
COPY workers/ ./workers

COPY packages/ ./packages

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=development \
    PATH=/opt/conda/envs/picogen2/bin:$PATH

CMD ["python", "-m", "workers/worker.py"]