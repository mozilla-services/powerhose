import sys
from powerhose.client.worker import Worker
from hashlib import sha512
from powerhose.jobrunner import _WORKERS_ENDPOINT

data = "wqidqibqwjibwx" * 100000


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
