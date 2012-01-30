import time
import sys
import zmq
import threading


endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://%s-routing.ipc"


class Pinger(threading.Thread):
    """ A Pinger that's used by a worker to Ping a Master
    """
    def __init__(self, identity, socket, locker, fail_callable,
                 duration=5., max_fails=10.):
        threading.Thread.__init__(self)
        self.duration = duration
        self.identity = identity
        self.socket = socket
        self.locker = locker
        self.running = False
        self.fail_callable = fail_callable
        self.max_fails = max_fails
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.disabled = False
        self.unresponsive = False

    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False

    def run(self):
        self.running = True
        num_failed = 0

        while self.running:
            if num_failed >= self.max_fails:
                self.unresponsive = True
                self.running = False
                break

            if self.disabled:
                time.sleep(1.)
                continue

            with self.locker:
                try:
                    self.socket.send_multipart(['PING', self.identity],
                                                zmq.NOBLOCK)
                except zmq.ZMQError, e:
                    num_failed += 1
                    continue

                try:
                    events = dict(self.poller.poll(self.duration * 1000))
                except zmq.ZMQError, e:
                    self.num_failed += 1
                    continue

                if len(events) == 0:
                    self.fail_callable()
                    num_failed += 1
                else:
                    for socket in events:
                        res = socket.recv()
                        if res != 'PONG':
                            self.running = False
                            self.fail_callable()
                            num_failed += 1

            time.sleep(self.duration)

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.join()
