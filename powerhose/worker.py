import time
import sys
import zmq
import threading

from powerhose.pinger import Pinger


endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://%s-routing.ipc"


class RegisterError(Exception):
    pass


class Worker(object):

    def __init__(self, identity, timeout=1.):
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

    def failed(self):
        print '**ping failed lets die'
        try:
            self._msg('REMOVE', 'REMOVED')
        except RegisterError:
            pass
        self.stop()

    def register(self):
        self._msg('READY', 'REGISTERED')
        self.registered = True

    def _msg(self, req, rep):
        self.pinger.disable()
        try:
            with self.locker:
                poller = zmq.Poller()
                poller.register(self.master, zmq.POLLIN)

                # ping the master we are online, with an ID
                try:
                    self.master.send_multipart([req, self.identity],
                                               zmq.NOBLOCK)
                except zmq.ZMQError:
                    raise RegisterError()

                try:
                    events = dict(poller.poll(self.timeout))
                except zmq.ZMQError:
                    raise RegisterError()

                if events == {}:
                    raise RegisterError()
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
        time.sleep(.5)
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
                msg = socket.recv_multipart()
                if msg == ['WAKE']:
                    # yeah I can work
                    socket.send('GIVE')
                elif msg[0] == 'JOB':
                    # do the job and send the result
                    print '%s is doing some work' % self.identity
                    socket.send_multipart(["JOBRES", msg[1], "RESULT"])

        self._msg('REMOVE', 'REMOVED')


if __name__ == '__main__':

    try:
        worker = Worker(workpoint % sys.argv[1])
        worker.run()
        worker.stop()
    except KeyboardInterrupt:
        worker.stop()
