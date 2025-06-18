FROM tanchihpin0517/picogen2:latest-full

RUN conda run -n picogen2
RUN pip install --upgrade pip
RUN pip install --no-cache-dir redis==5.0 rq==1.15 boto3

WORKDIR /app
COPY worker.py .

USER 10001

# replace with your actual environment variables when i get home
ENV CUDA_VISIBLE_DEVICES=0 \
    REDIS_URL=xxxx \
    ENVIRONMENT=development \
    AWS_CREDENTIALS=xxxxx\
    DATABASE_URL=xxxxx

    ENTRYPOINT ["conda", "run", "-n", "picogen2", "python", "worker.py"]