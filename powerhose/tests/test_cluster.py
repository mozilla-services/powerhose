# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import unittest

from powerhose import get_cluster
from powerhose.client import Client
from powerhose.exc import ExecutionError, TimeoutError


class TestCluster(unittest.TestCase):

    def setUp(self):
        self.clusters = []

    def tearDown(self):
        for cl in self.clusters:
            cl.stop()

    def _get_cluster(self, callable):
        front = 'ipc:///tmp/f-%s' % callable
        back = 'ipc:///tmp/b-%s' % callable
        hb = 'ipc:///tmp/h-%s' % callable
        cl = get_cluster(callable, frontend=front, backend=back, heartbeat=hb,
                         numprocesses=1, background=True)
        cl.start()
        self.clusters.append(cl)
        return Client(front)

    def test_error(self):
        client = self._get_cluster('powerhose.tests.jobs.fail')
        self.assertRaises(ExecutionError, client.execute, 'xx')

    def test_timeout(self):
        client = self._get_cluster('powerhose.tests.jobs.timeout')
        self.assertRaises(TimeoutError, client.execute, 'xx')

    def test_sucess(self):
        client = self._get_cluster('powerhose.tests.jobs.success')
        self.assertEqual(client.execute('xx'), 'xx')
