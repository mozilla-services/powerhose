# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import time
from threading import Thread
import contextlib

import zmq

from powerhose.util import unserialize
from powerhose import logger


class TimeoutError(Exception):
    pass


_WEIGHTS = range(10)


class Registration(Thread):
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
        client.identity = 'master-registration'
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
                        print('Registered %s' % msg[-1])
                        # keep track of that worker
                        work = self.context.socket(zmq.REQ)
                        work.connect(name)
                        work.identity = name
                        self.workers[name] = work

                    # in any case we pong back
                    logger.debug("[workermgr] sent a PONG")
                    socket.send('PONG')
                elif msg[-2] == 'REMOVE':
                    if msg[-1] in self.workers:
                        logger.debug("[workermgr] Removing` " + msg[-1])
                        del self.workers[msg[-1]]
                    socket.send('REMOVED')
                else:
                    logger.debug('Error')
                    socket.send('ERROR')

            time.sleep(.1)
