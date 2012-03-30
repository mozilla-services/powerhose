from powerhose.router import _ENDPOINT
from powerhose.job import Job
import random
import zmq

ctx = zmq.Context()
master = ctx.socket(zmq.REQ)
master.connect(_ENDPOINT)

while True:
    data = str(random.randint(1, 100000))
    job = Job(data)
    master.send(job.serialize())
    res = master.recv()
    assert res == data
    print '.'
