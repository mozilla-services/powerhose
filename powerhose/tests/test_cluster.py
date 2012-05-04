# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import unittest
import logging

from powerhose import get_cluster
from powerhose.client import Client
from powerhose.exc import ExecutionError, TimeoutError


logger = logging.getLogger('powerhose')


class TestCluster(unittest.TestCase):

    def setUp(self):
        self.clusters = []
        self.files = []

    def tearDown(self):
        logger.debug('stopping cluster')
        for cl in self.clusters:
            cl.stop()
        logger.debug('cluster stopped')

    def _get_cluster(self, callable):
        logger.debug('getting cluster')
        front = 'ipc:///tmp/f-%s' % callable
        back = 'ipc:///tmp/b-%s' % callable
        hb = 'ipc:///tmp/h-%s' % callable
        cl = get_cluster(callable, frontend=front, backend=back, heartbeat=hb,
                         numprocesses=1, background=True, debug=True)
        cl.start()
        self.clusters.append(cl)
        logger.debug('cluster ready')
        return Client(front, debug=True)

    def test_error(self):
        client = self._get_cluster('powerhose.tests.jobs.fail')
        self.assertRaises(ExecutionError, client.execute, 'xx')

    def test_timeout(self):
        client = self._get_cluster('powerhose.tests.jobs.timeout')
        self.assertRaises(TimeoutError, client.execute, 'xx')

    def test_success(self):
        client = self._get_cluster('powerhose.tests.jobs.success')
        self.assertEqual(client.execute('xx'), 'xx')

    def test_timeout_ovf(self):
        # this should work 1 time then fail
        client = self._get_cluster('powerhose.tests.jobs.timeout_overflow')
        self.assertEqual(client.execute('1.2'), 'xx')
        self.assertRaises(TimeoutError, client.execute, '1.2')

        # calling it back with the right execution time resets the counter
        self.assertEqual(client.execute('.1'), 'xx')
        self.assertEqual(client.execute('1.2'), 'xx')
        self.assertRaises(TimeoutError, client.execute, '1.2')
