import unittest
import time
from powerhose.heartbeat import Ping, Pong


class TestHeartbeat(unittest.TestCase):

    def test_working(self):
        beats = []
        lost = []

        def onbeat():
            beats.append('.')

        def onbeatlost():
            lost.append('.')

        pong = Pong('ipc:///tmp/ping.ipc', timeout=0.1)
        pong.start()
        time.sleep(.2)

        ping = Ping('ipc:///tmp/ping.ipc', onbeat=onbeat,
                    onbeatlost=onbeatlost,
                    delay=0.1)
        ping.start()

        time.sleep(5.)

        ping.stop()
        pong.stop()
        self.assertTrue(len(beats) > 10)
        self.assertEqual(len(lost),  0)

    def test_lost(self):
        beats = []
        lost = []

        def onbeat():
            beats.append('.')

        def onbeatlost():
            lost.append('.')

        pong = Pong('ipc:///tmp/ping.ipc', timeout=0.1)
        pong.start()
        time.sleep(.2)

        ping = Ping('ipc:///tmp/ping.ipc', onbeat=onbeat,
                    onbeatlost=onbeatlost,
                    delay=0.1)
        ping.start()

        time.sleep(2.)
        pong.stop()         # the ponger stops

        # the pinger continues for a while
        time.sleep(2.)

        ping.stop()

        self.assertTrue(len(beats) > 0)
        self.assertTrue(len(lost) > 3)
