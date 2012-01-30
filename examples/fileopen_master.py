from powerhose.jobrunner import JobRunner
import time
import sys
import random
import os


endpoint = "ipc://master-routing.ipc"


if __name__ == '__main__':

    files = [os.path.join('/etc', f) for f in os.listdir('/etc')]

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
            filecontent = runner.execute('1', random.choice(files))
            print 'File begins with %s' % filecontent[:100]


    except KeyboardInterrupt:
        runner.stop()
        print 'bye'
    except Exception, e:
        print str(e)
        print 'Something went wrong (are we still running workers?)'
        runner.stop()
        print 'bye'
