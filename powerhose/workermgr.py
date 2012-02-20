import time
import random
from threading import Thread, RLock
import contextlib
import zmq

from gevent.queue import Queue, Empty

from powerhose.util import serialize, unserialize


class TimeoutError(Exception):
    pass


_ENDPOINT = "ipc:///tmp/master-routing.ipc"
_WEIGHTS = range(10)


class Workers(object):

    def __init__(self, timeout=5.):
        self._available = Queue()
        self.timeout = timeout
        self._workers = {}

    def __contains__(self, worker):
        return worker in self._workers

    def __len__(self):
        return len(self._workers)

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

        worker = None

        # wait for timeout seconds
        try:
            while worker is None:
                worker = self._available.get(timeout=timeout)
                if worker.identity not in self._workers:
                    # it has been removed
                    self.delete(worker.identity)
                    worker = None

        except Empty:
            raise TimeoutError()

        return worker

    def delete(self, identity):
        if identity not in self._workers:
            return
        worker = self._workers[identity]
        del self._workers[identity]
        worker.close()

    def add(self, worker):
        self._available.put(worker)
        self._workers[worker.identity] = worker

    def release(self, worker):
        self._available.put(worker)


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
                msg = unserialize(socket.recv())
                print msg

                if len(msg) < 2:
                    # XXX log
                    socket.send('ERROR')

                if msg[-2] == 'PING':

                    if msg[-1] not in self.workers:
                        name = msg[-1]
                        # keep track of that worker
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)

                    # in any case we pong back
                    socket.send('PONG')
                elif msg[-2] == 'REMOVE':
                    if msg[-1] in self.workers:
                        self.workers.delete(msg[-1])
                    socket.send('REMOVED')
                else:
                    socket.send('ERROR')
