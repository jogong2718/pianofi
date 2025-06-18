FROM tanchihpin0517/picogen2:latest-full

RUN conda run -n picogen2
RUN pip install --upgrade pip
RUN pip install --no-cache-dir redis==5.0 \
    rq==1.15 \
    boto3 \
    sqlalchemy


WORKDIR /app
COPY worker.py .
COPY . /app/workers/
RUN mkdir -p /app/packages/

USER 10001

# replace with your actual environment variables when i get home
ENV CUDA_VISIBLE_DEVICES=0 \
    ENVIRONMENT=development

ENTRYPOINT ["conda", "run", "-n", "picogen2", "python", "worker.py"]