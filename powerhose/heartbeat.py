# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import threading
import zmq
import time
import os

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
                 onbeatlost=None, onbeat=None,):
        threading.Thread.__init__(self)
        self.daemon = True
        self.context = zmq.Context()
        self.endpoint = endpoint
        self.running = False
        self.delay = delay
        self.retries = retries
        self.onbeatlost = onbeatlost
        self.onbeat = onbeat
        self.warmup_delay = warmup_delay
        self._endpoint = self.context.socket(zmq.SUB)
        logger.debug('Subscribing to ' + self.endpoint)
        self._endpoint.setsockopt(zmq.SUBSCRIBE, '')
        self._endpoint.linger = 0
        self._endpoint.identity = str(os.getpid())
        self._endpoint.connect(self.endpoint)
        self._poller = zmq.Poller()
        self._poller.register(self._endpoint, zmq.POLLIN)

    def start(self):
        """Starts the pinger"""
        threading.Thread.start(self)

    def run(self):
        time.sleep(self.warmup_delay)
        self.running = True
        while self.running:
            # waiting for the BEAT
            tries = 0
            logger.debug('Waiting for the BEAT')

            while tries < self.retries:
                events = dict(self._poller.poll(self.delay * 1000))

                if events != {}:
                    break

                logger.debug('nothing came back')
                tries += 1
                if tries == self.retries:
                    if self.onbeatlost is not None and self.onbeatlost():
                        self.running = False
                        return

            if events and events[self._endpoint] == zmq.POLLIN:
                msg = self._endpoint.recv()
                if self.onbeat is not None:
                    self.onbeat()
                logger.debug(msg)

        logger.debug('Ping loop over')

    def stop(self):
        """Stops the Pinger"""
        #logger.debug('Stopping the Pinger')
        self.running = False
        self.join()


class Heartbeat(threading.Thread):
    """Class that implements a ZMQ heartbeat server.

    Options:

    - **endpoint** : The ZMQ socket to call.
    - **interval** : Interval between two beat.
    """
    def __init__(self, endpoint=DEFAULT_HEARTBEAT, interval=2.):
        threading.Thread.__init__(self)
        self.daemon = True
        self.context = zmq.Context()
        self.endpoint = endpoint
        self.running = False
        self.interval = interval
        logger.debug('Publishing to ' + self.endpoint)
        self._endpoint = self.context.socket(zmq.PUB)
        self._endpoint.linger = 0
        self._endpoint.identity = b'HB'
        self._endpoint.hwm = 0
        self._endpoint.bind(self.endpoint)

    def start(self):
        """Starts the Pong service"""
        threading.Thread.start(self)

    def run(self):
        self.running = True
        while self.running:
            self._endpoint.send('BEAT')
            logger.debug('*beat*')
            time.sleep(self.interval)

    def stop(self):
        """Stops the Pong service"""
        self.running = False
        self.join()
