import time
import threading

from gevent_zeromq import zmq

from powerhose.client.pinger import Pinger
from powerhose.util import serialize, unserialize
from powerhose import logger


class RegisterError(Exception):
    pass


class Worker(object):

    def __init__(self, endpoint, identity, target, timeout=1.):
        self.identity = identity
        self.ctx = zmq.Context()
        self.timeout = timeout * 1000
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(endpoint)
        self.work = self.ctx.socket(zmq.REP)
        self.work.bind(identity)
        self.registered = self.running = False
        # setting a poller
        self.poller = zmq.Poller()
        self.poller.register(self.work, zmq.POLLIN)
        self.locker = threading.RLock()
        self.pinger = Pinger(self.identity, self.master, self.locker,
                             self.failed)
        self.target = target

    def failed(self):
        logger.debug("ping failed let's die")
        try:
            self._msg('REMOVE', 'REMOVED')
        except RegisterError:
            pass
        self.stop()

    def register(self):
        self._msg('PING', 'PONG')
        self.registered = True

    def _msg(self, req, rep):
        self.pinger.disable()
        try:
            with self.locker:
                poller = zmq.Poller()
                poller.register(self.master, zmq.POLLIN)

                # ping the master we are online, with an ID
                try:
                    data = serialize(req, self.identity)
                    self.master.send(data, zmq.NOBLOCK)
                except zmq.ZMQError, e:
                    raise RegisterError(str(e))

                try:
                    events = dict(poller.poll(self.timeout))
                except zmq.ZMQError, e:
                    raise RegisterError(str(e))

                if events == {}:
                    raise RegisterError("Nothing came back")
                else:
                    for socket in events:
                        res = socket.recv()
                        if res != rep:
                            raise RegisterError(res)
        finally:
            self.pinger.enable()

    def stop(self):
        self.running = False
        self.pinger.stop()
        time.sleep(.1)
        self.ctx.destroy(0)

    def run(self):
        self.running = True
        self.register()
        self.pinger.start()

        while self.running and not self.pinger.unresponsive:
            try:
                events = dict(self.poller.poll(self.timeout))
            except zmq.ZMQError:
                break

            for socket in events:
                msg = unserialize(socket.recv())

                logger.debug(msg)
                if msg[0] == 'JOB':
                    # do the job and send the result
                    start = time.time()
                    try:
                        res = self.target(msg[1:])
                    except Exception, e:
                        # XXX log the error
                        res = str(e)
                    logger.debug('%.6f' % (time.time() - start))
                    socket.send(serialize("JOBRES", msg[1], res))
                else:
                    socket.send('ERROR')

        try:
            self._msg('REMOVE', 'REMOVED')
        except RegisterError:
            pass
