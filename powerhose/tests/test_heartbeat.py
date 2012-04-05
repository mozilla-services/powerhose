import unittest
import time
from powerhose.heartbeat import Stethoscope, Heartbeat


class TestHeartbeat(unittest.TestCase):

    def test_working(self):
        beats = []
        lost = []

        def onbeat():
            beats.append('.')

        def onbeatlost():
            lost.append('.')

        hb = Heartbeat('ipc:///tmp/stetho.ipc', interval=0.1)
        hb.start()
        time.sleep(.2)

        stetho = Stethoscope('ipc:///tmp/stetho.ipc', onbeat=onbeat,
                    onbeatlost=onbeatlost,
                    delay=0.1)
        stetho.start()

        time.sleep(5.)

        stetho.stop()
        hb.stop()
        self.assertTrue(len(beats) > 10)
        self.assertEqual(len(lost),  0)

    def test_lost(self):
        beats = []
        lost = []

        def onbeat():
            beats.append('.')

        def onbeatlost():
            lost.append('.')

        hb = Heartbeat('ipc:///tmp/stetho.ipc', interval=0.1)
        hb.start()
        time.sleep(.2)

        stetho = Stethoscope('ipc:///tmp/stetho.ipc', onbeat=onbeat,
                    onbeatlost=onbeatlost,
                    delay=0.1)
        stetho.start()

        time.sleep(2.)
        hb.stop()         # the hber stops

        # the stethoer continues for a while
        time.sleep(2.)

        stetho.stop()

        self.assertTrue(len(beats) > 0)
        self.assertTrue(len(lost) > 3)
