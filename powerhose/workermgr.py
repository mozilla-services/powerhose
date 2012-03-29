# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import time
from threading import Thread
import contextlib

import zmq
from gevent.queue import Queue, Empty

from powerhose.util import unserialize
from powerhose import logger


class TimeoutError(Exception):
    pass


_WEIGHTS = range(10)


class Workers(object):
    """Queue of workers.

    Provides a context manager to assign a worker to a job.

    Options:

    - **timeout**: time in seconds to try to get a worker from the
      queue after that time, a :class:`TimeoutError` exception is
      thrown.
    """
    def __init__(self, timeout=5.):
        self._available = Queue()
        self.timeout = timeout
        self._workers = {}

    def __contains__(self, worker):
        return worker in self._workers

    def __len__(self):
        return len(self._workers)

    @contextlib.contextmanager
    def get_context(self, timeout=None):
        """Context manager to get a worker.


        :func:`get_context` uses :func:`acquire` and
        :func:`release`.

        Options:

        - **timeout**: time in second before raising a TimeoutError
          exception. Defaults to the value provided in the class
          initialization.

        Example::

            workers = Workers()
            with workers.get_context() as worker:
               ... do something with the worker ...

        """
        _worker = self.acquire(timeout)
        try:
            yield _worker
        finally:
            self.release(_worker)

    def acquire(self, timeout=None):
        """Acquire a worker from the queue and remove it.

        Should be used with :func:`release`.

        Options:

        - **timeout**: time in second before raising a TimeoutError
          exception. Defaults to the value provided in the class
          initialization.
        """
        logger.debug('Trying to acquire a worker')
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
            raise TimeoutError("Could not get a worker")

        logger.debug('we got one \o/')
        return worker

    def delete(self, identity):
        """Close a worker and remove it from the queue.

        Options:

        - **identity**: the worker identity.
        """

        if identity not in self._workers:
            return
        worker = self._workers[identity]
        del self._workers[identity]
        worker.close()

    def add(self, worker):
        """Put a worker in the queue.

        Options:

        - **worker**: the worker to put.
        """
        self._available.put(worker)
        self._workers[worker.identity] = worker

    def release(self, worker):
        """Put back the worker in the queue.

        Options:

        - **worker**: the worker to put back.

        Should be used with :func:`acquire`.
        """
        logger.debug('releasing the worker')
        self._available.put(worker)


class WorkerRegistration(Thread):
    """Thread that manages the worker registration channel.

    Options:

    - **workers**: the :class:`Workers` instance the thread will work with.
    - **endpoint**: the ZMQ endpoint to use as a registration channel.
    """
    def __init__(self, workers, endpoint):
        Thread.__init__(self)
        self.workers = workers
        self.context = zmq.Context()
        self.alive = False
        self.endpoint = endpoint

    def stop(self):
        """Stop the thread -- thus the registration
        """
        logger.debug('Stopping [workermgr]')
        self.alive = False
        self.join()

    def run(self):
        """Runs the registration.

        Should not be called directly. Use :func:`start`.
        """
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
