from powerhose.jobrunner import JobRunner
import time
import sys
import random

endpoint = "ipc://master-routing.ipc"


if __name__ == '__main__':

    runner = JobRunner(endpoint)
    runner.start()

    try:
        # wait to have at least 1 worker
        print 'Waiting for some workers to register -- run square_worker.py'
        while len(runner.workers) == 0:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.)

        print
        while True:
            print runner.execute('1', str(random.randrange(1000)))

    except KeyboardInterrupt:
        runner.stop()
        print 'bye'
    except Exception, e:
        import pdb; pdb.set_trace()
        print str(e)
        print 'Something went wrong (are we still running workers?)'
        runner.stop()
        print 'bye'
