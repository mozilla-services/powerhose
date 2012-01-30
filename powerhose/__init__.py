from powerhose.jobrunner import JobRunner
import time


if __name__ == '__main__':
    runner = JobRunner()
    runner.start()

    try:
        while len(runner.workers) < 1:
            print 'waiting for workers'
            time.sleep(1.)

        while True:
            print runner.execute(1, "SOMEDATA")
            #time.sleep(1.)
    finally:
        runner.stop()
