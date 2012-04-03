# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" Jobs runner.
"""
import time
import sys
import traceback
import argparse

from zmq.eventloop import ioloop, zmqstream
import zmq


from powerhose import logger
from powerhose.util import send, recv, set_logger, register_ipc_file
from powerhose.heartbeat import Pong


_FRONTEND = "ipc:///tmp/powerhose-front.ipc"
_BACKEND = "ipc:///tmp/powerhose-back.ipc"
_HEARTBEAT = "ipc:///tmp/powerhose-beat.ipc"


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
    def __init__(self, frontend=_FRONTEND, backend=_BACKEND,
                 heartbeat=_HEARTBEAT):
        logger.debug('Initializing the broker.')

        for endpoint in (frontend, backend, heartbeat):
            if endpoint.startswith('ipc'):
                register_ipc_file(endpoint)

        self.context = zmq.Context(io_threads=2)

        # setting up the two sockets
        self._frontend = self.context.socket(zmq.ROUTER)
        self._frontend.bind(frontend)
        self._backend = self.context.socket(zmq.DEALER)
        self._backend.bind(backend)

        # setting up the poller
        #self.poller = zmq.Poller()
        #self.poller.register(self._frontend, zmq.POLLIN)
        #self.poller.register(self._backend, zmq.POLLIN)
        self.loop = ioloop.IOLoop()
        self._frontstream = zmqstream.ZMQStream(self._frontend, self.loop)
        self._frontstream.on_recv(self._handle_recv_front)
        self._backstream = zmqstream.ZMQStream(self._backend, self.loop)
        self._backstream.on_recv(self._handle_recv_back)

        # heartbeat
        self.pong = Pong(heartbeat)

        # status
        self.started = False
        self.poll_timeout = None

    def _handle_recv_front(self, msg):
        # front => back
        logger.debug('front -> back')
        self._backstream.send_multipart(msg)

    def _handle_recv_back(self, msg):
        # back => front
        logger.debug('front <- back')
        self._frontstream.send_multipart(msg)

    def start(self):
        """Starts the registration loop and then wait for some job.
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

            #try:
            #    socks = dict(self.poller.poll(self.poll_timeout))
            #except zmq.ZMQError, e:
            #    logger.debug("The poll failed")
            #    logger.debug(str(e))
            #    break

            #try:
            #    if socks.get(self._frontend) == zmq.POLLIN:
            #        logger.debug('front -> back')
            #        message = recv(self._frontend)
            #        more = self._frontend.getsockopt(zmq.RCVMORE)
            #        send(self._backend, message, more)#

            #    if socks.get(self._backend) == zmq.POLLIN:
            #        logger.debug('front <- back')
            #        message = recv(self._backend)
            #        more = self._backend.getsockopt(zmq.RCVMORE)
            #        send(self._frontend, message, more)
            #except Exception, e:
            #    # we don't want to die on error. we just log it
            #    exc_type, exc_value, exc_traceback = sys.exc_info()
            #    exc = traceback.format_tb(exc_traceback)
            #    exc.insert(0, str(e))
            #    logger.error('\n'.join(exc))

    def stop(self):
        """Stops the registration loop.
        """
        if not self.started:
            return
        self.loop.stop()
        self.pong.stop()
        self.started = False


def main(args=sys.argv):
    parser = argparse.ArgumentParser(description='Powerhose broker.')

    parser.add_argument('--frontend', dest='frontend', default=_FRONTEND,
                        help="ZMQ socket to receive jobs.")

    parser.add_argument('--backend', dest='backend',
                        default=_BACKEND,
                        help="ZMQ socket for workers.")

    parser.add_argument('--heartbeat', dest='heartbeat',
                        default=_HEARTBEAT,
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
