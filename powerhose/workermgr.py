import time
from threading import Thread
import contextlib

from gevent_zeromq import zmq
from gevent.queue import Queue, Empty

from powerhose.util import unserialize
from powerhose import logger


class TimeoutError(Exception):
    pass


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
            raise TimeoutError("Could not get a worker out "
                                "of %d workers" % len(self._available))

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

    def __init__(self, workers, endpoint):
        Thread.__init__(self)
        self.workers = workers
        self.context = zmq.Context()
        self.alive = False
        self.endpoint = endpoint

    def stop(self):
        logger.debug('Stopping [workermgr]')
        self.alive = False
        self.join()

    def run(self):
        self.alive = True

        # channel to communicate with the workers
        logger.debug('Starting [workermgr]')
        client = self.context.socket(zmq.REP)
        client.identity = 'master'
        client.bind(self.endpoint)
        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)
        poll_timeout = 1000

        while self.alive:
            try:
                events = dict(poller.poll(poll_timeout))
            except zmq.ZMQError, e:
                logger.debug("The poll failed")
                logger.debug(str(e))
                break

            for socket in events:
                msg = unserialize(socket.recv())

                if len(msg) < 2:
                    # XXX log
                    socket.send('ERROR')

                if msg[-2] == 'PING':
                    logger.debug("[workermgr] Got a PING")
                    if msg[-1] not in self.workers:
                        name = msg[-1]
                        logger.debug("Registered " + name)
                        # keep track of that worker
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)

                    # in any case we pong back
                    logger.debug("[workermgr] sent a PONG")
                    socket.send('PONG')
                elif msg[-2] == 'REMOVE':
                    if msg[-1] in self.workers:
                        logger.debug("[workermgr] Removing` " + msg[-1])
                        self.workers.delete(msg[-1])
                    socket.send('REMOVED')
                else:
                    logger.debug('Error')
                    socket.send('ERROR')

            time.sleep(.1)
