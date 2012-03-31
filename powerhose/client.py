import random
import zmq

from powerhose.router import _ENDPOINT
from powerhose.job import Job


class Client(object):

    def __init__(self, endpoint=_ENDPOINT):
        self.ctx = zmq.Context()
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(_ENDPOINT)

    def execute(self, job):
        if isinstance(job, str):
            job = Job(job)
        self.master.send(job.serialize())
        return self.master.recv()
