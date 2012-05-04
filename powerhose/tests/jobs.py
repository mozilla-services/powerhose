# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import time
import sys


def _p(msg):
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()


def fail(job):
    _p('Starting powerhose.tests.jobs.fail')
    try:
        raise ValueError(job.data)
    finally:
        _p('Ending powerhose.tests.jobs.fail')


def timeout(job):
    _p('Starting powerhose.tests.jobs.timeout')
    time.sleep(2.)
    try:
        return job.data
    finally:
        _p('Ending powerhose.tests.jobs.timeout')


def timeout_overflow(job):
    _p('Starting powerhose.tests.jobs.timeout_overflow')
    time.sleep(float(job.data))
    try:
        return 'xx'
    finally:
        _p('Ending powerhose.tests.jobs.timeout_overflow')


def success(job):
    _p('Starting powerhose.tests.jobs.success')
    try:
        return job.data
    finally:
        _p('Ending powerhose.tests.jobs.success')
