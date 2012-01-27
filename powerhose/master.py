import time
import random
from threading import Thread, RLock
import contextlib
from gevent.queue import PriorityQueue, Empty
import zmq


class TimeoutError(Exception):
    pass


_ENDPOINT = "ipc://master-routing.ipc"
_WORKPOINT = "ipc://%s-routing.ipc"
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
            print 'choosing in ' + str(self._available.keys())
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
        print 'delete a worker ' + worker

        if worker in self._workers:
            self._workers.remove(worker)

        if worker in self._busy:
            self._busy[worker]

        if worker in self._available:
            _worker = self._available[worker]
            _worker.close()
            del self._available[worker]
        print 'got left ' + str(self._available.keys())


    def add(self, worker):
        print 'adding a worker ' + worker.identity
        self._available[worker.identity] = worker
        self._workers.append(worker.identity)

    def release(self, worker):
        print 'releasing'
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
                break # interrupted

            if events == {}:
                print 'no event'

            for socket in events:
                msg = socket.recv_multipart()
                if msg[-2] == 'PING':
                    print 'PONG => ' + socket.identity
                    if msg[-1] not in self.workers:
                        name = msg[-1]
                        # keep track of that worker
                        print 'adding worker %s' % name
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)
                        print 'REGISTERED => ' + socket.identity

                    socket.send('PONG')
                elif msg[-2] == 'READY':
                    if msg[-1] in self.workers:
                        print 'already registered'
                    else:
                        name = msg[-1]
                        # keep track of that worker
                        print 'adding worker %s' % name
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers.add(work)
                        print 'REGISTERED => ' + socket.identity

                    socket.send('REGISTERED')

                elif msg[-2] == 'REMOVE':
                    print '<= REMOVE'
                    if msg[-1] in self.workers:
                        workers.delete(msg[-1])
                        print 'REMOVED => ' + socket.identity
                    socket.send('REMOVED')
                elif msg[-2] == 'PING' and msg[-1] in self.workers:
                    print 'PONG => ' + socket.identity
                    socket.send('PONG')
                else:
                    print 'not implem. ' + str(msg)


class JobRunner(object):
    def __init__(self, workers, retries=3):
        self.workers = workers
        self.retries = retries

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
                print 'WAKE => ' + worker.identity
                try:
                    worker.send("WAKE", zmq.NOBLOCK)  # XXX if this fails we want to try another one
                except zmq.ZMQError, e:
                    print 'wake failed ' + str(e)
                    # we want to ditch this one !
                    raise TimeoutError()

                poller = zmq.Poller()
                poller.register(worker, zmq.POLLIN)

                while True:
                    try:
                        events = dict(poller.poll(timeout*1000.))
                    except zmq.ZMQError:
                        print 'interrupted'
                        break # interrupted

                    if events == {}:
                        print 'nothing to see'
                        if time.time() - now > timeout:
                            raise TimeoutError()

                    for socket in events:
                        msg = socket.recv_multipart()
                        if msg == ['GIVE']:
                            print 'GIVE <= ' + worker.identity
                            # the worker is ready to get some job done
                            print 'JOB => ' + worker.identity
                            socket.send_multipart(["JOB", str(job_id), job_data],
                                                zmq.NOBLOCK)
                        elif msg[0] == 'JOBRES':
                            # we got a result
                            print 'JOBRES <= ' + worker.identity
                            return msg[-1]
                        else:
                            raise NotImplementedError(str(msg))

                raise TimeoutError()
        except:
            if worker is not None:
                # killing this worker - it can come back on the next ping
                workers.delete(worker.identity)
            raise



if __name__ == '__main__':
    workers = Workers()
    registration = WorkerRegistration(workers)
    runner = JobRunner(workers)
    registration.start()

    try:
        while len(workers) < 1:
            print 'waiting for workers'
            time.sleep(1.)

        while True:
            print runner.execute(1, "SOMEDATA")
            #time.sleep(1.)
    finally:
        registration.stop()
