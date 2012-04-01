import zmq

from powerhose.broker import _FRONTEND, TimeoutError
from powerhose.job import Job
from powerhose.util import send, recv
from powerhose import logger


class Client(object):

    def __init__(self, frontend=_FRONTEND, timeout=.5):
        self.ctx = zmq.Context()
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(frontend)
        logger.debug('Client connected to %s' % frontend)
        self.poller = zmq.Poller()
        self.poller.register(self.master, zmq.POLLIN)
        self.timeout = timeout * 1000

    def execute(self, job):
        if isinstance(job, str):
            job = Job(job)

        send(self.master, job.serialize())

        socks = dict(self.poller.poll(self.timeout))

        if socks.get(self.master) == zmq.POLLIN:
            return recv(self.master)

        raise TimeoutError()
