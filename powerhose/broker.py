# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" Jobs runner.
"""
import errno
import sys
import traceback
import argparse

from zmq.eventloop import ioloop, zmqstream
import zmq

from powerhose.util import (set_logger, register_ipc_file, DEFAULT_FRONTEND,
                            DEFAULT_BACKEND, DEFAULT_HEARTBEAT, logger)
from powerhose.heartbeat import Heartbeat


class Broker(object):
    """Class that route jobs to workers.

    Options:

    - **frontend**: the ZMQ socket to receive jobs.
    - **backend**: the ZMQ socket to communicate with workers.
    - **heartbeat**: the ZMQ socket to receive heartbeat requests/
    """
    def __init__(self, frontend=DEFAULT_FRONTEND, backend=DEFAULT_BACKEND,
                 heartbeat=DEFAULT_HEARTBEAT):
        logger.debug('Initializing the broker.')

        for endpoint in (frontend, backend, heartbeat):
            if endpoint.startswith('ipc'):
                register_ipc_file(endpoint)

        self.context = zmq.Context()

        # setting up the two sockets
        self._frontend = self.context.socket(zmq.ROUTER)
        self._frontend.bind(frontend)
        self._backend = self.context.socket(zmq.DEALER)
        self._backend.bind(backend)

        # setting up the poller
        self.loop = ioloop.IOLoop()
        self._frontstream = zmqstream.ZMQStream(self._frontend, self.loop)
        self._frontstream.on_recv(self._handle_recv_front)
        self._backstream = zmqstream.ZMQStream(self._backend, self.loop)
        self._backstream.on_recv(self._handle_recv_back)

        # heartbeat
        self.pong = Heartbeat(heartbeat)

        # status
        self.started = False
        self.poll_timeout = None

    def _handle_recv_front(self, msg):
        # front => back
        logger.debug('front -> back')
        try:
            self._backstream.send_multipart(msg)
        except Exception, e:
            # we don't want to die on error. we just log it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc = traceback.format_tb(exc_traceback)
            exc.insert(0, str(e))
            logger.error('\n'.join(exc))

    def _handle_recv_back(self, msg):
        # back => front
        logger.debug('front <- back')
        try:
            self._frontstream.send_multipart(msg)
        except Exception, e:
            # we don't want to die on error. we just log it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exc = traceback.format_tb(exc_traceback)
            exc.insert(0, str(e))
            logger.error('\n'.join(exc))

    def start(self):
        """Starts the broker.
        """
        logger.debug('Starting the loop')
        if self.started:
            return

        # running the heartbeat
        self.pong.start()

        self.started = True
        while self.started:
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
        """Stops the broker.
        """
        if not self.started:
            return
        self.loop.stop()
        self.pong.stop()
        self.started = False


def main(args=sys.argv):
    parser = argparse.ArgumentParser(description='Powerhose broker.')

    parser.add_argument('--frontend', dest='frontend',
                        default=DEFAULT_FRONTEND,
                        help="ZMQ socket to receive jobs.")

    parser.add_argument('--backend', dest='backend',
                        default=DEFAULT_BACKEND,
                        help="ZMQ socket for workers.")

    parser.add_argument('--heartbeat', dest='heartbeat',
                        default=DEFAULT_HEARTBEAT,
                        help="ZMQ socket for the heartbeat.")

    parser.add_argument('--debug', action='store_true', default=False,
                        help="Debug mode")

    parser.add_argument('--logfile', dest='logfile', default='stdout',
                        help="File to log in to .")

    args = parser.parse_args()

    set_logger(args.debug, logfile=args.logfile)
    logger.info('Starting the broker')
    broker = Broker(frontend=args.frontend, backend=args.backend,
                    heartbeat=args.heartbeat)
    logger.info('Listening to incoming jobs at %r' % args.frontend)
    logger.info('Workers may register at %r' % args.backend)
    logger.info('The heartbeat socket is at %r' % args.heartbeat)
    try:
        broker.start()
    except KeyboardInterrupt:
        pass
    finally:
        broker.stop()


if __name__ == '__main__':
    main()
