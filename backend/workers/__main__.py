from .audio_worker import AudioWorker

if __name__ == '__main__':
    worker = AudioWorker()
    worker.start()