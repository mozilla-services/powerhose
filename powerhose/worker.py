# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import errno
import time
import os
import sys
import traceback
import argparse
import logging

import zmq

from powerhose import util
from powerhose.util import (logger, set_logger, DEFAULT_BACKEND,
                            DEFAULT_HEARTBEAT)
from powerhose.job import Job
from powerhose.util import resolve_name, decode_params
from powerhose.heartbeat import Stethoscope

from zmq.eventloop import ioloop, zmqstream


class Worker(object):
    """Class that links a callable to a broker.

    Options:

    - **target**: The Python callable that will be called when the broker
      send a job.
    - **backend**: The ZMQ socket to connect to the broker.
    - **heartbeat**: The ZMQ socket to perform PINGs on the broker to make
      sure it's still alive.
    - **ping_delay**: the delay in seconds betweem two pings.
    - **ping_retries**: the number of attempts to ping the broker before
      quitting.
    - **params** a dict containing the params to set for this worker.
    """
    def __init__(self, target, backend=DEFAULT_BACKEND,
                 heartbeat=DEFAULT_HEARTBEAT, ping_delay=1., ping_retries=3,
                 params=None):
        logger.debug('Initializing the worker.')
        self.ctx = zmq.Context()
        self.backend = backend
        self._backend = self.ctx.socket(zmq.REP)
        self._backend.connect(self.backend)
        self.target = target
        self.running = False
        self.loop = ioloop.IOLoop()
        self._backstream = zmqstream.ZMQStream(self._backend, self.loop)
        self._backstream.on_recv(self._handle_recv_back)
        self.ping = Stethoscope(heartbeat, onbeatlost=self.lost,
                                delay=ping_delay, retries=ping_retries)
        self.debug = logger.isEnabledFor(logging.DEBUG)
        self.params = params

    def _handle_recv_back(self, msg):
        # do the job and send the result
        if self.debug:
            logger.debug('Job received')
            start = time.time()

        try:
            res = self.target(Job.load_from_string(msg[0]))
        except Exception, e:
            # in case of an error, we're building a message
            # that's prefixed with ERROR:
            #
            # This message will be re-raised on the other side
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc = traceback.format_tb(exc_traceback)
            exc.insert(0, str(e))
            res = 'ERROR:' + '\n'.join(exc)
            logger.error(res)

        if self.debug:
            logger.debug('%.6f' % (time.time() - start))

        try:
            self._backstream.send(res)
        except Exception:
            logging.error("Could not send back the result", exc_info=True)

    def lost(self):
        logger.info('Master lost ! Quitting..')
        self.running = False
        self.loop.stop()
        return True

    def stop(self):
        """Stops the worker.
        """
        logger.debug('Stopping the worker')
        self.ping.stop()
        self.loop.stop()
        self.running = False
        time.sleep(.1)
        self.ctx.destroy(0)
        logger.debug('Worker is stopped')

    def start(self):
        """Starts the worker
        """
        util.PARAMS = self.params

        logger.debug('Starting the worker loop')

        # running the pinger
        self.ping.start()
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

        logger.debug('Worker loop over')


def main(args=sys.argv):

    parser = argparse.ArgumentParser(description='Run some watchers.')

    parser.add_argument('--backend', dest='backend',
                        default=DEFAULT_BACKEND,
                        help="ZMQ socket to the broker.")

    parser.add_argument('target', help="Fully qualified name of the callable.")

    parser.add_argument('--debug', action='store_true', default=False,
                        help="Debug mode")

    parser.add_argument('--logfile', dest='logfile', default='stdout',
                        help="File to log in to.")

    parser.add_argument('--heartbeat', dest='heartbeat',
                        default=DEFAULT_HEARTBEAT,
                        help="ZMQ socket for the heartbeat.")

    parser.add_argument('--params', dest='params', default=None,
                        help='The parameters to be used in the worker.')

    args = parser.parse_args()
    set_logger(args.debug, logfile=args.logfile)
    sys.path.insert(0, os.getcwd())  # XXX
    target = resolve_name(args.target)
    if args.params is None:
        params = {}
    else:
        params = decode_params(args.params)

    logger.info('Worker registers at %s' % args.backend)
    logger.info('The heartbeat socket is at %r' % args.heartbeat)
    worker = Worker(target, backend=args.backend, heartbeat=args.heartbeat,
                    params=params)

    try:
        worker.start()
    except KeyboardInterrupt:
        return 1
    finally:
        worker.stop()

    return 0


if __name__ == '__main__':
    main()
