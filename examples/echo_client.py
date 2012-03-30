import random
import sys

from powerhose.client import Client
from powerhose.job import Job


client = Client()

while True:
    data = str(random.randint(1, 100000))
    job = Job(data)
    res = client.execute(job)
    assert res == data
    sys.stdout.write('.')
    sys.stdout.flush()
