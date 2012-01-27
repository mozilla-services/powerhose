import time
import random
from threading import Thread, RLock
import contextlib

import zmq


class TimeoutError(Exception):
    pass


_ENDPOINT = "ipc://master-routing.ipc"
_WORKPOINT = "ipc://%s-routing.ipc"


class Workers(dict):

    def __init__(self):
        self.lock = RLock()

    @contextlib.contextmanager
    def worker(self):
        _worker = self.acquire()
        yield _worker
        self.release(_worker)

    def acquire(self):
        with self.lock:
            key = random.choice(workers.keys())
            worker = workers[key]
            del workers[key]
            return worker

    def add(self, worker):
        with self.lock:
            workers[worker.identity] = worker

    def release(self, worker):
        with self.lock:
            workers[worker.identity] = worker

    def delete(self, name):
        with self.lock:
            worker = workers[name]
            worker.close()
            del workers[name]


class WorkerRegistration(Thread):

    def __init__(self, workers, endpoint=_ENDPOINT):
        Thread.__init__(self)
        self.workers = workers
        self.context = zmq.Context()
        self.alive = False
        self.endpoint = endpoint

    def stop(self):
        self.alive = False
        self.join()

    def run(self):
        self.alive = True

        # channel to communicate with the workers
        client = self.context.socket(zmq.REP)
        client.identity = 'master'
        client.bind(self.endpoint)

        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)

        while self.alive:
            try:
                events = dict(poller.poll(1000))
            except zmq.ZMQError:
                break # interrupted

            for socket in events:
                msg = socket.recv_multipart()
                if msg[-2] == 'READY' and msg[-1] not in workers:
                    name = msg[-1]
                    # keep track of that worker
                    print 'adding worker %s' % name
                    work = self.context.socket(zmq.REQ)
                    work.connect(name)
                    work.identity = name
                    workers.add(work)
                    socket.send('REGISTERED')
                elif msg[-2] == 'REMOVE' and msg[-1] in workers:
                    delete_worker(msg[-1])


class JobRunner(object):
    def __init__(self, workers):
        self.workers = workers

    def execute(self, job_id, job_data, timeout=1.):
        # errors out if we don't have any worker registered
        if len(self.workers) == 0:
            raise ValueError("No Workers!")

        with self.workers.worker() as worker:
            print 'sending some work at ' + worker.identity

            worker.send("WAKE")  # XXX if this fails we want to try another one

            poller = zmq.Poller()
            poller.register(worker, zmq.POLLIN)

            while True:
                try:
                    events = dict(poller.poll(timeout*1000.))
                except zmq.ZMQError:
                    break # interrupted

                for socket in events:
                    msg = socket.recv_multipart()
                    if msg == ['GIVE']:
                        # the worker is ready to get some job done
                        socket.send_multipart(["JOB", str(job_id), job_data])
                    elif msg[0] == 'JOBRES':
                        # we got a result
                        return msg[-1]
                    else:
                        raise NotImplementedError(str(msg))

            raise TimeoutError()


if __name__ == '__main__':
    workers = Workers()
    registration = WorkerRegistration(workers)
    runner = JobRunner(workers)
    registration.start()

    try:
        while len(workers) < 2:
            print 'waiting for workers'
            time.sleep(1.)

        for x in range(1000):
            print runner.execute(x, "SOMEDATA")
    finally:
        registration.stop()
