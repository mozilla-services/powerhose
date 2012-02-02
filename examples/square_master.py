from powerhose.jobrunner import JobRunner
import time
import sys
import random

endpoint = "ipc:///tmp/master-routing.ipc"


if __name__ == '__main__':

    runner = JobRunner(endpoint)
    runner.start()

    try:
        # wait to have at least 1 worker
        print 'Waiting for some workers to register -- run square_worker.py'
        while len(runner.workers) < 1:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.)

        while True:
            print runner.execute('1', str(random.randrange(1000)))

        runner.stop()
    except KeyboardInterrupt:
        runner.stop()
        print 'bye'
    except Exception, e:
        print str(e)
        print 'Something went wrong (are we still running workers?)'
        runner.stop()
        print 'bye'
