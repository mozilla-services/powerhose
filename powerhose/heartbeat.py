import threading
import zmq
import time

from powerhose.util import send, recv, register_ipc_file
from powerhose.exc import TimeoutError
from powerhose import logger


class Ping(threading.Thread):

    def __init__(self, endpoint, warmup_delay=.5, delay=1., retries=3,
                 onbeatlost=None, onbeat=None):
        threading.Thread.__init__(self)
        self.daemon = True
        if endpoint.startswith('ipc:'):
            register_ipc_file(endpoint)
        self.context = zmq.Context()
        self._endpoint = self.context.socket(zmq.REQ)
        self._endpoint.connect(endpoint)
        self.running = False
        self.delay = delay
        self.retries = retries
        self.onbeatlost = onbeatlost
        self.onbeat = onbeat
        self.warmup_delay = warmup_delay

    def run(self):
        time.sleep(self.warmup_delay)

        self.running = True

        while self.running:
            # sending a PING
            try:
                send(self._endpoint, 'PING', max_retries=self.retries,
                     retry_sleep=self.delay)
            except TimeoutError:
                if self.onbeatlost is not None:
                    if self.onbeatlost():
                        self.running = False
                continue

            # waiting for the PONG
            try:
                res = recv(self._endpoint, max_retries=self.retries,
                        retry_sleep=self.delay)
            except TimeoutError:
                if self.onbeatlost is not None:
                    if self.onbeatlost():
                        self.running = False
                continue

            if res != 'PONG':       # wat ?
                if self.onbeatlost is not None:
                    if self.onbeatlost():
                        self.running = False
                continue

            if self.running:
                # worked
                if self.onbeat is not None:
                    self.onbeat()

                logger.debug('Pinged!')
                time.sleep(self.delay)

        logger.debug('Ping loop over')

    def stop(self):
        logger.debug('Stopping the pinger')
        self.running = False
        self.context.destroy(0)
        self.join()


class Pong(threading.Thread):
    def __init__(self, endpoint, timeout=5.):
        threading.Thread.__init__(self)
        self.daemon = True
        self.context = zmq.Context(io_threads=2)
        if endpoint.startswith('ipc:'):
            register_ipc_file(endpoint)
        self._endpoint = self.context.socket(zmq.REP)
        self._endpoint.bind(endpoint)
        self.poller = zmq.Poller()
        self.poller.register(self._endpoint, zmq.POLLIN)
        self.running = False
        self.timeout = timeout

    def run(self):
        self.running = True

        while self.running:
            try:
                events = dict(self.poller.poll(self.timeout * 1000))
            except zmq.ZMQError, e:
                logger.debug("The poll failed")
                logger.debug(str(e))
                break

            if len(events) == 0:
                continue

            try:
                msg = recv(self._endpoint)
            except TimeoutError:
                continue    # ah well...

            if msg != 'PING':       # wat ?
                continue   # ah well


            send(self._endpoint, 'PONG')
            logger.debug('Ponged!')

    def stop(self):
        self.running = False
        time.sleep(self.timeout)
        self.context.destroy(0)
        self.join()
