from rq import Worker, Queue
import redis
import os

class AudioWorker:
    def __init__(self):
        self.redis_conn = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379))
        )
        self.queue = Queue('audio_processing', connection=self.redis_conn)
        self.worker = Worker([self.queue], connection=self.redis_conn)
    
    def start(self):
        print("Audio worker started, waiting for jobs...")