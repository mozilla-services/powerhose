import random
import sys
import time
import threading

from powerhose.client import Pool
from powerhose.job import Job
from powerhose.util import set_logger
from powerhose.exc import NoWorkerError



class Worker(threading.Thread):

    def __init__(self, pool):
        threading.Thread.__init__(self)
        self.pool = pool
        self.running = False

    def run(self):
        i = 0
        self.running = True

        while self.running:
            data = str(random.randint(1, 1000))
            job = Job(data)
            sys.stdout.write(str(i) +  '-> ')
            sys.stdout.flush()
            try:
                res = self.pool.execute(job)
            except NoWorkerError:
                sys.stdout.write('NO WORKER\n')
            else:
                assert res == data
                sys.stdout.write('OK\n')
            sys.stdout.flush()
            i += 1

    def stop(self):
        self.running = False
        self.join()


if __name__ == '__main__':
    # a pool of 10 workers
    client = Pool()

    # 10 threads hammering the broker
    workers = [Worker(client) for i in range(20)]
    for worker in workers:
        worker.start()

    # just sit there for 100 seconds
    try:
        time.sleep(3600)
    finally:
        for worker in workers:
            worker.stop()


