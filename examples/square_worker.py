from powerhose.jobrunner import JobRunner
from powerhose.client.worker import Worker

import time

endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://worker-routing.ipc"



if __name__ == '__main__':

    def square(*args):
        number = int((args)[0][1])
        return str(number * number)

    worker = Worker(endpoint, workpoint, target=square)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()

