import zmq

from powerhose.exc import TimeoutError
from powerhose.job import Job
from powerhose.util import send, recv, DEFAULT_FRONTEND, logger


class Client(object):
    """Class to call a Powerhose cluster.

    Options:

    - **frontend**: ZMQ socket to call.
    - **timeout**: maximum allowed time for a job to run.
      Defaults to 5s.
    """
    def __init__(self, frontend=DEFAULT_FRONTEND, timeout=5.):
        self.ctx = zmq.Context(io_threads=2)
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(frontend)
        logger.debug('Client connected to %s' % frontend)
        self.poller = zmq.Poller()
        self.poller.register(self.master, zmq.POLLIN)
        self.timeout = timeout * 1000

    def execute(self, job, timeout=None):
        """Runs the job

        Options:

        - **job**: Job to be performed. Can be a :class:`Job`
          instance or a string. If it's a string a :class:`Job` instance
          will be automatically created out of it.
        - **timeout**: maximum allowed time for a job to run.
          If not provided, uses the one defined in the constructor.

        If the job fails after the timeout, raises a :class:`TimeoutError`.
        """
        if isinstance(job, str):
            job = Job(job)

        if timeout is None:
            timeout = self.timeout

        send(self.master, job.serialize())

        socks = dict(self.poller.poll(timeout))

        if socks.get(self.master) == zmq.POLLIN:
            return recv(self.master)

        raise TimeoutError()
