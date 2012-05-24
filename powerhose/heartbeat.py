# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import threading
import errno
import time

import zmq
from zmq.eventloop import ioloop, zmqstream

from powerhose.util import logger, DEFAULT_HEARTBEAT


class Stethoscope(threading.Thread):
    """Class that implements a ZMQ heartbeat client.

    Options:

    - **endpoint** : The ZMQ socket to call.
    - **warmup_delay** : The delay before starting to Ping. Defaults to 5s.
    - **delay**: The delay between two pings. Defaults to 3s.
    - **retries**: The number of attempts to ping. Defaults to 3.
    - **onbeatlost**: a callable that will be called when a ping failed.
      If the callable returns **True**, the ping quits. Defaults to None.
    - **onbeat**: a callable that will be called when a ping succeeds.
      Defaults to None.
    """
    def __init__(self, endpoint=DEFAULT_HEARTBEAT, warmup_delay=.5, delay=3.,
                 retries=3,
                 onbeatlost=None, onbeat=None, io_loop=None):
        threading.Thread.__init__(self)
        self.loop = io_loop or ioloop.IOLoop.instance()
        self._stop_loop = io_loop is None
        self.daemon = True
        self.context = zmq.Context()
        self.endpoint = endpoint
        self.running = False
        self.delay = delay
        self.retries = retries
        self.onbeatlost = onbeatlost
        self.onbeat = onbeat
        self.warmup_delay = warmup_delay
        self._endpoint = None
        self._stream = None
        self._timer = None
        self.tries = 0

    def _initialize(self):
        logger.debug('Subscribing to ' + self.endpoint)
        self._endpoint = self.context.socket(zmq.SUB)
        self._endpoint.setsockopt(zmq.SUBSCRIBE, '')
        self._endpoint.linger = 0
        #self._endpoint.identity = str(os.getpid())
        self._endpoint.connect(self.endpoint)
        self._stream = zmqstream.ZMQStream(self._endpoint, self.loop)
        self._stream.on_recv(self._handle_recv)
        self._timer = ioloop.PeriodicCallback(self._delayed,
                self.delay * 1000, io_loop=self.loop)

    def _delayed(self):
        self.tries += 1
        if self.tries >= self.retries:
            logger.debug('Nothing came back')
            if self.onbeatlost is None or self.onbeatlost():
                self.stop()   # bye !

    def _handle_recv(self, msg):
        self.tries = 0
        if self.onbeat is not None:
            self.onbeat()
        logger.debug(msg[0])

    def run(self):
        """Starts the loop"""
        logger.debug('Starting the loop')
        if self.running:
            return

        self._initialize()
        time.sleep(self.warmup_delay)
        self._timer.start()
        self.running = True
        while self.running:
            try:
                self.loop.start()
            except zmq.ZMQError as e:
                logger.debug(str(e))

                if e.errno == errno.EINTR:
                    continue
                elif e.errno == zmq.ETERM:
                    break
                else:
                    logger.debug("got an unexpected error %s (%s)", str(e),
                                 e.errno)
                    raise
            else:
                break

    def stop(self):
        """Stops the Pinger"""
        logger.debug('Stopping the Pinger')
        self.running = False
        self._stream.flush()
        if self._stop_loop:
            self.loop.stop()
        if self.isAlive():
            try:
                self.join()
            except RuntimeError:
                pass


class Heartbeat(object):
    """Class that implements a ZMQ heartbeat server.

    This class sends in a ZMQ socket regular beats.

    Options:

    - **endpoint** : The ZMQ socket to call.
    - **interval** : Interval between two beat.
    """
    def __init__(self, endpoint=DEFAULT_HEARTBEAT, interval=2.,
                 io_loop=None):
        self.loop = io_loop or ioloop.IOLoop.instance()
        self.daemon = True
        self.context = zmq.Context()
        self.endpoint = endpoint
        self.running = False
        self.interval = interval
        logger.debug('Publishing to ' + self.endpoint)
        self._endpoint = self.context.socket(zmq.PUB)
        self._endpoint.linger = 0
        #self._endpoint.identity = b'HB'
        self._endpoint.hwm = 0
        self._endpoint.bind(self.endpoint)
        self._cb = ioloop.PeriodicCallback(self._ping, interval * 1000,
                                           io_loop=self.loop)

    def start(self):
        """Starts the Pong service"""
        self.running = True
        self._cb.start()

    def _ping(self):
        logger.debug('*beat*')
        self._endpoint.send('BEAT')

    def stop(self):
        """Stops the Pong service"""
        self.running = False
        self._cb.stop()
        self.context.destroy(0)
