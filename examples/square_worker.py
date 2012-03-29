import sys
from powerhose.client.worker import Worker


endpoint = "ipc:///tmp/master-routing.ipc"
#workpoint = "ipc://worker-routing.ipc"


if __name__ == '__main__':
    try:
        workpoint = sys.argv[1]
    except:
        print(sys.argv)
        raise

    def square(job):
        number = int(job.data)
        return str(number * number)

    worker = Worker(endpoint, workpoint, target=square)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()
