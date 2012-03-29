from powerhose.jobrunner import JobRunner
from powerhose.job import Job

import time
import sys
import random

endpoint = "ipc:///tmp/master-routing.ipc"
_NUM = 10000


if __name__ == '__main__':

    runner = JobRunner(endpoint)
    runner.start()

    try:
        # wait to have at least 2 worker
        print 'Waiting for 2+ workers to register -- run square_worker.py'
        while len(runner.workers) < 2:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.)

        num = str(random.randrange(1000))
        start = time.time()
        for i in range(_NUM):
            runner.execute(Job(num))
            sys.stdout.write('.')
            sys.stdout.flush()

        end = time.time() - start
        print('It took %.2f seconds to run %d jobs' % (end, _NUM))
        runner.stop()
    except KeyboardInterrupt:
        runner.stop()
        print 'bye'
    except Exception, e:
        print str(e)
        print 'Something went wrong (are we still running workers?)'
        runner.stop()
        print 'bye'
