# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import unittest
import logging
import os
import tempfile
import time

from powerhose import get_cluster
from powerhose.exc import ExecutionError, TimeoutError
from powerhose import client


logger = logging.getLogger('powerhose')


class TestCluster(unittest.TestCase):

    def setUp(self):
        self.clusters = []
        self.files = []
        self.old_timeout = client.DEFAULT_TIMEOUT
        self.old_movf = client.DEFAULT_TIMEOUT_MOVF
        self.old_ovf = client.DEFAULT_TIMEOUT_OVF
        client.DEFAULT_TIMEOUT = .5
        client.DEFAULT_TIMEOUT_MOVF = 1.
        client.DEFAULT_TIMEOUT_OVF = 1
        self.overflow = str(client.DEFAULT_TIMEOUT + .2)
        self.moverflow = str(client.DEFAULT_TIMEOUT_MOVF + .2)

    def tearDown(self):
        logger.debug('stopping cluster')
        for cl in self.clusters:
            cl.stop()
        for fl in self.files:
            os.remove(fl)
        logger.debug('cluster stopped')
        client.DEFAULT_TIMEOUT = self.old_timeout
        client.DEFAULT_TIMEOUT_MOVF = self.old_movf
        client.DEFAULT_TIMEOUT_OVF = self.old_ovf

    def _get_file(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)
        self.files.append(path)
        return path

    def _get_cluster(self, callable, **kw):
        logger.debug('getting cluster')
        front = 'ipc:///tmp/f-%s' % callable
        back = 'ipc:///tmp/b-%s' % callable
        hb = 'ipc:///tmp/h-%s' % callable
        cl = get_cluster(callable, frontend=front, backend=back, heartbeat=hb,
                         numprocesses=1, background=True, debug=True,
                         timeout=client.DEFAULT_TIMEOUT_MOVF, **kw)
        cl.start()
        self.clusters.append(cl)
        logger.debug('cluster ready')
        return client.Client(front, debug=True, timeout=client.DEFAULT_TIMEOUT,
                timeout_max_overflow=client.DEFAULT_TIMEOUT_MOVF,
                timeout_overflows=client.DEFAULT_TIMEOUT_OVF)

    def test_error(self):
        client = self._get_cluster('powerhose.tests.jobs.fail')
        self.assertRaises(ExecutionError, client.execute, 'xx')

    def test_timeout(self):
        client = self._get_cluster('powerhose.tests.jobs.timeout_overflow')
        self.assertRaises(TimeoutError, client.execute, self.moverflow)

    def test_success(self):
        client = self._get_cluster('powerhose.tests.jobs.success')
        self.assertEqual(client.execute('xx'), 'xx')

    def test_timeout_ovf(self):
        # this should work 1 time then fail
        file = self._get_file()
        client = self._get_cluster('powerhose.tests.jobs.timeout_overflow',
                                   logfile=file)

        try:
            self.assertEqual(client.execute(self.overflow), 'xx')
        except Exception:
            with open(file) as f:
                raise Exception(f.read())

        try:
            self.assertRaises(TimeoutError, client.execute, self.overflow)
        except Exception:
            with open(file) as f:
                raise Exception(f.read())

        # calling it back with the right execution time resets the counter
        self.assertEqual(client.execute('.1'), 'xx')
        self.assertEqual(client.execute(self.overflow), 'xx')
        self.assertRaises(TimeoutError, client.execute, self.overflow)

    def test_timeout_dump(self):
        file = self._get_file()
        client = self._get_cluster('powerhose.tests.jobs.timeout_overflow',
                                    logfile=file)

        self.assertRaises(TimeoutError, client.execute, self.moverflow)
        time.sleep(1.)      # give the worker a chance to dump the stack

        with open(file) as f:
            res = [line.strip() for line in f.readlines() if line.strip()]

        # the worker should be blocked on the sleep
        self.assertTrue('time.sleep(float(job.data))' in res)
