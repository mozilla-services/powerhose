# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import unittest
from powerhose.job import Job


class TestJob(unittest.TestCase):

    def test_job(self):
        job = Job('somedata', {'one': '1'})
        data = job.serialize()
        job2 = Job.load_from_string(data)
        self.assertTrue(job.data, job2.data)
        self.assertTrue(job.headers.items(), job2.headers.items())
