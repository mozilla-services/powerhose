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
        cl = get_cluster(callable, numprocesses=1, background=True)
        cl.start()
        self.clusters.append(cl)

    def test_error(self):
        self._get_cluster('powerhose.tests.jobs.fail')
        client = Client()
        self.assertRaises(ExecutionError, client.execute, 'xx')

    def test_timeout(self):
        self._get_cluster('powerhose.tests.jobs.timeout')
        client = Client()
        self.assertRaises(TimeoutError, client.execute, 'xx')

    def test_sucess(self):
        self._get_cluster('powerhose.tests.jobs.success')
        client = Client()
        self.assertEqual(client.execute('xx'), 'xx')
