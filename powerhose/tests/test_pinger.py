import unittest
import zmq
import threading
import time

from powerhose.pinger import Pinger


_ENDPOINT = 'ipc:///tmp/tests.ipc'


class Ponger(threading.Thread):
    def __init__(self, ctx):
        threading.Thread.__init__(self)
        self.socket = ctx.socket(zmq.REP)
        self.socket.bind(_ENDPOINT)
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.count = 0

    def run(self):
        while self.count < 5:
            try:
                events = dict(self.poller.poll(100))
            except zmq.ZMQError:
                break

            for socket in events:
                msg = socket.recv_multipart()

                if msg[-2] == 'PING':
                    socket.send('PONG')
                    self.count += 1
                else:
                    socket.send('ERROR')


class TestPinger(unittest.TestCase):

    def _test_pinging(self):
        ctx = zmq.Context()
        locker = threading.RLock()
        socket = ctx.socket(zmq.REQ)
        socket.connect(_ENDPOINT)

        ponger = Ponger(ctx)
        failures = [0]

        def failed():
            failures[0] += 1

        ponger.start()
        time.sleep(0.2)

        pinger = Pinger('me', socket, locker, failed, duration=0.1)
        pinger.start()
        time.sleep(0.2)

        ponger.join()
        ctx.destroy(0)
        pinger.stop()

        # let's see how many ping we did
        self.assertEqual(ponger.count, 5)

    def test_too_many_failures(self):
        ctx = zmq.Context()
        locker = threading.RLock()
        socket = ctx.socket(zmq.REQ)
        socket.connect(_ENDPOINT)
        failures = [0]

        def failed():
            failures[0] += 1

        pinger = Pinger('me', socket, locker, failed, duration=0.1)
        pinger.start()

        time.sleep(1.)

        # pinging 10 times nowwhere will make the pinger quit
        #pinger.join()
        ctx.destroy(0)

        self.assertTrue(len(failures), 10)
        self.assertTrue(pinger.unresponsive)
