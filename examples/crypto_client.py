import os
import sys
import binascii
import random

from powerhose.client import Client
from powerhose.job import Job


algs = ('ECDSA256', 'Ed25519', 'RSA2048', 'RSA3248')

client = Client()

def run():
    data = binascii.b2a_hex(os.urandom(256))[:256]
    job = Job(data + '--' + random.choice(algs))
    return client.execute(job)

while True:
    res = run()
    sys.stdout.write('.')
    sys.stdout.flush()
