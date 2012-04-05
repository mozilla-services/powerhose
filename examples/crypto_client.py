import os
import sys
import binascii
import random
import time

from powerhose.client import Client
from powerhose.job import Job
from powerhose.util import set_logger


set_logger(True)
algs = ('ECDSA256', 'Ed25519', 'RSA2048', 'RSA3248')
client = Client()


def run():
    data = binascii.b2a_hex(os.urandom(256))[:256]
    job = Job(data + '--' + random.choice(algs))
    return client.execute(job)


print 'Running 100 crypto'
start = time.time()


for i in range(100):
    res = run()
    sys.stdout.write('.')
    sys.stdout.flush()

print 'Done in %.2f' % (time.time() - start)
