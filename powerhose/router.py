# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" Jobs runner.
"""
import time
import zmq
import sys
import traceback
import random

from powerhose.registration import Registration
from powerhose.util import serialize, unserialize, register_ipc_file
from powerhose import logger


class TimeoutError(Exception):
    pass


class ExecutionError(Exception):
    pass



_ENDPOINT = "ipc:///tmp/powerhose-routing.ipc"
_WORKERS_ENDPOINT = "ipc:///tmp/powerhose-registration.ipc"


def timed(func):
    def _timed(*args, **kw):
        from powerhose import logger
        start = time.time()
        try:
            return func(*args, **kw)
        finally:
            logger.debug('%.4f' % (time.time() - start))
    return _timed


class Router(object):
    """Class that sends jobs to workers.

        Router does two things:

        1. runs a :class:`Registration` instance which is
           responsible for the registration of workers.

        2. offers a method to execute jobs.

        Options:

        - **endpoint**: The ZMQ endpoint for receiving Jobs.

        - **workers_endpoint**: The ZMQ endpoint for workers registration.
          (default: ipc://master-routing.ipc)

        - **retries**: The number of retries when a job fails.
          (default: 3)
    """
    def __init__(self, endpoint=_ENDPOINT,
                 workers_endpoint=_WORKERS_ENDPOINT, retries=3):
        if endpoint.startswith('ipc'):
            register_ipc_file(endpoint)

        if workers_endpoint.startswith('ipc'):
            register_ipc_file(workers_endpoint)

        self.context = zmq.Context()
        self.started = False
        self.endpoint = endpoint
        self.workers_endpoint = workers_endpoint
        self.workers = {}
        self.registration = Registration(self.workers,
                                         self.workers_endpoint)
        self.retries = retries

    def start(self):
        """Starts the registration loop and then wait for some job.
        """
        if self.started:
            return

        logger.debug('Starting registration at ' + self.endpoint)
        self.registration.start()
        logger.debug('Starting Job channel.')
        client = self.context.socket(zmq.REP)
        client.identity = 'master'
        client.bind(self.endpoint)
        poller = zmq.Poller()
        poller.register(client, zmq.POLLIN)
        poll_timeout = 1000
        self.started = True

        # XXX where to put this ...
        while len(self.workers) == 0:
            time.sleep(0.1)


        while self.started:
            try:
                events = dict(poller.poll(poll_timeout))
            except zmq.ZMQError, e:
                logger.debug("The poll failed")
                logger.debug(str(e))
                break

            for socket in events:
                job = socket.recv()
                socket.send(self._execute(job))

    def stop(self):
        """Stops the registration loop.
        """
        if not self.started:
            return
        logger.debug('Stopping registration at ' + self.endpoint)
        self.registration.stop()
        self.started = False

    def _execute(self, job, timeout=1.):
        """Execute a job and return the result.

        Options:

        - **job**: a :class:`Job` instance.
        - **timeout**: the maximum allowed time in seconds. (default: 1)

        If the job fails to run, this method may raise one of these
        exceptions:

        - :class:`TimeoutError`: timed out.
        - :class:`ExecutionError`: the worker has failed.

        In case of an execution error, the exception usually holds
        more details on the failure.
        """
        from powerhose import logger
        e = None

        for i in range(self.retries):
            try:
                return self.__execute(job, timeout)
            except (TimeoutError, ExecutionError), e:
                logger.debug(str(e))
                logger.debug('retrying - %d' % (i + 1))

        if e is not None:
            raise e

    @timed
    def __execute(self, job, timeout=1.):
        worker = None
        timeout *= 1000.   # timeout is in ms
        data = serialize("JOB", job)
        try:
            logger.debug('getting a worker')
            worker = random.choice(self.workers.values())
            try:
                worker.send(data, zmq.NOBLOCK)
            except zmq.ZMQError, e:
                raise ExecutionError(str(e))

            poller = zmq.Poller()
            poller.register(worker, zmq.POLLIN)

            try:
                events = dict(poller.poll(timeout))
            except zmq.ZMQError, e:
                raise ExecutionError(str(e))

            if events == {}:
                raise TimeoutError()

            for socket in events:
                try:
                    msg = unserialize(socket.recv())
                except zmq.ZMQError, e:
                    raise ExecutionError(str(e))

                if msg[0] == 'JOBRES':
                    # we got a result
                    return msg[-1]
                else:
                    raise NotImplementedError(str(msg))

        except Exception, e:
            logger.debug('something went wrong')

            if worker is not None:
                # killing this worker - it can come back on the next ping
                del self.workers[worker.identity]

            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc = traceback.format_tb(exc_traceback)
            exc.insert(0, str(e))
            raise ExecutionError('\n'.join(exc))
