from powerhose.jobrunner import JobRunner, _ENDPOINT
from powerhose.job import Job
from hashlib import sha512
import zmq
import time
import sys
import random

_NUM = 100

data = "wqidqibqwjibwx" * 1000

ctx = zmq.Context()
timeout = 5 * 1000

master = ctx.socket(zmq.REQ)
master.connect(_ENDPOINT)
job = Job(data)
data = job.serialize()

while True:
    data = str(random.randint(1, 100000))
    job = Job(data)
    master.send(job.serialize())
    res = master.recv()
    assert res == data
    print '.'
