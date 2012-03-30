from powerhose.router import _ENDPOINT
import random
import zmq


class Client(object):

    def __init__(self, endpoint=_ENDPOINT):
        self.ctx = zmq.Context()
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(_ENDPOINT)

    def execute(self, job):
        self.master.send(job.serialize())
        return self.master.recv()
