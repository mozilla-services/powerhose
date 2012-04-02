# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import time
import os
import sys
import traceback
import argparse

import zmq

from powerhose.broker import _BACKEND
from powerhose.util import unserialize, set_logger
from powerhose import logger
from powerhose.job import Job
from powerhose.util import send, resolve_name


class Worker(object):

    def __init__(self, backend, target, timeout=1.):
        self.ctx = zmq.Context()
        self.timeout = timeout * 1000
        self.backend = backend
        self._backend = self.ctx.socket(zmq.REP)
        self._backend.connect(self.backend)
        self.target = target
        self.running = False
        self.poller = zmq.Poller()
        self.poller.register(self._backend, zmq.POLLIN)
        self.poll_timeout = None

    def stop(self):
        self.running = False
        time.sleep(.1)
        self.ctx.destroy(0)

    def start(self):
        self.running = True

        logger.debug('Starting the loop')
        while self.running:
            try:
                socks = dict(self.poller.poll(self.poll_timeout))
            except zmq.ZMQError, e:
                logger.debug("The poll failed")
                logger.debug(str(e))
                break
            try:
                if socks.get(self._backend) == zmq.POLLIN:

                    msg = unserialize(self._backend.recv())

                    # do the job and send the result
                    start = time.time()
                    try:
                        res = self.target(Job.load_from_string(msg[0]))
                    except Exception, e:
                        # XXX log the error
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        exc = traceback.format_tb(exc_traceback)
                        exc.insert(0, str(e))
                        res = '\n'.join(exc)
                        logger.error(res)

                    logger.debug('%.6f' % (time.time() - start))

                    send(self._backend, res)
            except Exception, e:
                # we don't want to die on socket error. we just log them
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exc = traceback.format_tb(exc_traceback)
                exc.insert(0, str(e))
                logger.error('\n'.join(exc))


def main(args=sys.argv):

    parser = argparse.ArgumentParser(description='Run some watchers.')

    parser.add_argument('--backend', dest='backend', default=_BACKEND,
                        help="ZMQ socket to the broker.")
    parser.add_argument('target', help="Fully qualified name of the callable.")
    parser.add_argument('--debug', action='store_true', default=False,
                        help="Debug mode")
    parser.add_argument('--logfile', dest='logfile', default='stdout',
                        help="File to log in to .")

    args = parser.parse_args()
    set_logger(args.debug, logfile=args.logfile)
    sys.path.insert(0, os.getcwd())  # XXX
    target = resolve_name(args.target)

    logger.info('Worker registers at %s' % args.backend)
    worker = Worker(args.backend, target=target)

    try:
        worker.start()
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()


if __name__ == '__main__':
    main()
