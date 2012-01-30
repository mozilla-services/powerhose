import time
import random
from threading import Thread, RLock
import contextlib
import zmq

from powerhose.workermgr import Workers, WorkerRegistration


class TimeoutError(Exception):
    pass

_ENDPOINT = "ipc://master-routing.ipc"


class JobRunner(object):
    def __init__(self, endpoint=_ENDPOINT, retries=3):
        self.workers = Workers()
        self.registration = WorkerRegistration(self.workers)
        self.retries = retries

    def start(self):
        self.registration.start()

    def stop(self):
        self.registration.stop()

    def execute(self, job_id, job_data, timeout=1.):
        for i in range(self.retries):
            try:
                return self._execute(job_id, job_data, timeout)
            except TimeoutError:

                time.sleep(0.1)

        raise TimeoutError()

    def _execute(self, job_id, job_data, timeout=1.):
        now = time.time()

        # errors out if we don't have any worker registered
        #if len(self.workers) == 0:
        #    raise ValueError("No Workers!")
        worker = None
        try:
            with self.workers.worker() as worker:
                try:
                    worker.send("WAKE", zmq.NOBLOCK)
                except zmq.ZMQError, e:
                    raise TimeoutError()

                poller = zmq.Poller()
                poller.register(worker, zmq.POLLIN)

                while True:
                    try:
                        events = dict(poller.poll(timeout * 1000.))
                    except zmq.ZMQError:
                        break

                    # XXX replace by an alarm to avoid
                    # using cpu cycles
                    if events == {}:
                        if time.time() - now > timeout:
                            raise TimeoutError()

                    for socket in events:
                        msg = socket.recv().split(':::')
                        if msg == ['GIVE']:
                            # the worker is ready to get some job done
                            socket.send(':::'.join(["JOB", str(job_id),
                                                    job_data]),
                                        zmq.NOBLOCK)

                        elif msg[0] == 'JOBRES':
                            # we got a result
                            return msg[-1]
                        else:
                            raise NotImplementedError(str(msg))

                raise TimeoutError()
        except:
            if worker is not None:
                # killing this worker - it can come back on the next ping
                self.workers.delete(worker.identity)
            raise
