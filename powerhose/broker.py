# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" Jobs runner.
"""
import time
import zmq
import sys
import traceback
import argparse

from powerhose import logger
from powerhose.util import send, recv, set_logger, register_ipc_file


_FRONTEND = "ipc:///tmp/powerhose-front.ipc"
_BACKEND = "ipc:///tmp/powerhose-back.ipc"


def timed(func):
    def _timed(*args, **kw):
        from powerhose import logger
        start = time.time()
        try:
            return func(*args, **kw)
        finally:
            logger.debug('%.4f' % (time.time() - start))
    return _timed


class Broker(object):
    """Class that route jobs to workers.

    """
    def __init__(self, frontend=_FRONTEND, backend=_BACKEND):
        logger.debug('Initializing the broker.')

        for endpoint in (frontend, backend):
            if endpoint.startswith('ipc'):
                register_ipc_file(endpoint)

        self.context = zmq.Context()

        # setting up the two sockets
        self._frontend = self.context.socket(zmq.ROUTER)
        self._frontend.bind(frontend)
        self._backend = self.context.socket(zmq.DEALER)
        self._backend.bind(backend)

        # setting up the poller
        self.poller = zmq.Poller()
        self.poller.register(self._frontend, zmq.POLLIN)
        self.poller.register(self._backend, zmq.POLLIN)

        # status
        self.started = False
        self.poll_timeout = None

    def start(self):
        """Starts the registration loop and then wait for some job.
        """
        logger.debug('Starting the loop')
        if self.started:
            return

        self.started = True
        while self.started:
            try:
                socks = dict(self.poller.poll(self.poll_timeout))
            except zmq.ZMQError, e:
                logger.debug("The poll failed")
                logger.debug(str(e))
                break

            try:
                if socks.get(self._frontend) == zmq.POLLIN:
                    logger.debug('front -> back')
                    message = recv(self._frontend)
                    more = self._frontend.getsockopt(zmq.RCVMORE)
                    send(self._backend, message, more)

                if socks.get(self._backend) == zmq.POLLIN:
                    logger.debug('front <- back')
                    message = recv(self._backend)
                    more = self._backend.getsockopt(zmq.RCVMORE)
                    send(self._frontend, message, more)
            except Exception, e:
                # we don't want to die on error. we just log it
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exc = traceback.format_tb(exc_traceback)
                exc.insert(0, str(e))
                logger.error('\n'.join(exc))

    def stop(self):
        """Stops the registration loop.
        """
        if not self.started:
            return
        self.started = False


def main(args=sys.argv):
    parser = argparse.ArgumentParser(description='Powerhose broker.')

    parser.add_argument('--frontend', dest='frontend', default=_FRONTEND,
                        help="ZMQ socket to receive jobs.")

    parser.add_argument('--backend', dest='backend',
                        default=_BACKEND,
                        help="ZMQ socket for workers.")

    parser.add_argument('--debug', action='store_true', default=False,
                        help="Debug mode")

    parser.add_argument('--logfile', dest='logfile', default='stdout',
                        help="File to log in to .")

    args = parser.parse_args()

    set_logger(args.debug, logfile=args.logfile)
    logger.info('Starting the broker')
    broker = Broker(frontend=args.frontend, backend=args.backend)
    logger.info('Listening to incoming jobs at %s' % args.frontend)
    logger.info('Workers may register at %s' % args.backend)
    try:
        broker.start()
    except KeyboardInterrupt:
        pass
    finally:
        broker.stop()


if __name__ == '__main__':
    main()
