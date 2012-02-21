import time
import random
from threading import Thread, RLock
import contextlib
from gevent_zeromq import zmq

from powerhose.workermgr import Workers, WorkerRegistration
from powerhose.util import serialize, unserialize


class TimeoutError(Exception):
    pass


class ExecutionError(Exception):
    pass


_ENDPOINT = "ipc://master-routing.ipc"


def timed(func):
    def _timed(*args, **kw):
        from powerhose import logger
        start = time.time()
        try:
            return func(*args, **kw)
        finally:
            logger.debug('%.4f' % (time.time() - start))
    return _timed


class JobRunner(object):
    def __init__(self, endpoint=_ENDPOINT, retries=3):
        self.started = False
        self.workers = Workers()
        self.registration = WorkerRegistration(self.workers)
        self.retries = retries

    def start(self):
        if self.started:
            return
        self.registration.start()
        self.started = True

    def stop(self):
        if not self.started:
            return
        self.registration.stop()
        self.started = False

    def execute(self, job_id, job_data, timeout=1.):
        from powerhose import logger
        e = None

        for i in range(self.retries):
            try:

                return self._execute(job_id, job_data, timeout)
            except (TimeoutError, ExecutionError), e:
                logger.debug(str(e))
                logger.debug('retrying - %d' % (i + 1))

        if e is not None:
            raise e

    # XXX timeout is for each poll()
    @timed
    def _execute(self, job_id, job_data, timeout=1.):
        worker = None
        timeout *= 1000.   # timeout is in ms
        data = serialize("JOB", str(job_id), job_data)

        try:
            with self.workers.worker() as worker:
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
            if worker is not None:
                # killing this worker - it can come back on the next ping
                self.workers.delete(worker.identity)

            raise ExecutionError(str(e))
