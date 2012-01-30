from powerhose.jobrunner import JobRunner
from powerhose.client.worker import Worker

import time

endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://worker-routing.ipc"



if __name__ == '__main__':

    def fileopen(*args):
        filename = args[0][1]
        with open(filename) as f:
            return f.read()

    worker = Worker(endpoint, workpoint, target=fileopen)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()

