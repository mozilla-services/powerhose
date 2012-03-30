import sys

from powerhose.router import _WORKERS_ENDPOINT
from powerhose.worker import Worker


if __name__ == '__main__':
    try:
        workpoint = sys.argv[1]
    except:
        print(sys.argv)
        raise

    def square(job):
        return job.data

    worker = Worker(_WORKERS_ENDPOINT, workpoint, target=square)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()
