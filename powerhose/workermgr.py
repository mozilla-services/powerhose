import time
import random
from threading import Thread, RLock
import contextlib
import zmq


class TimeoutError(Exception):
    pass


_ENDPOINT = "ipc://master-routing.ipc"
_WEIGHTS = range(10)


class Workers(object):

    def __init__(self, timeout=5.):
        self.lock = RLock()
        self._available = {}
        self._busy = {}
        self.timeout = timeout
        self._workers = []

    def __contains__(self, worker):
        return worker in self._workers

    def __len__(self):
        return len(self._available) + len(self._busy)

    @contextlib.contextmanager
    def worker(self):
        _worker = self.acquire()
        try:
            yield _worker
        finally:
            self.release(_worker)

    def acquire(self, timeout=None):
        if timeout is None:
            timeout = self.timeout

        # need to catch the empty exception
        tries = 0
        worker = key = None

        while worker is None and tries < 3:
            try:
                key = random.choice(self._available.keys())
                worker = self._available[key]
                del self._available[key]
            except IndexError:
                tries += 1

        if worker is None:
            raise ValueError()

        self._busy[key] = worker
        return worker

    def delete(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

        if worker in self._busy:
            self._busy[worker]

        if worker in self._available:
            _worker = self._available[worker]
            _worker.close()
            del self._available[worker]

    def add(self, worker):
        self._available[worker.identity] = worker
        self._workers.append(worker.identity)

    def release(self, worker):
        del self._busy[worker.identity]
        self._available[worker.identity] = worker


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
                break

            for socket in events:
                msg = socket.recv_multipart()
                if msg[-2] == 'PING':
                    if msg[-1] not in self.workers:
                        name = msg[-1]
                        # keep track of that worker
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)

                    socket.send('PONG')
                elif msg[-2] == 'READY':
                    if msg[-1] not in self.workers:
                        name = msg[-1]
                        # keep track of that worker
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)

                    socket.send('REGISTERED')

                elif msg[-2] == 'REMOVE':
                    if msg[-1] in self.workers:
                        workers.delete(msg[-1])
                    socket.send('REMOVED')
                else:
                    socket.send('ERROR')
