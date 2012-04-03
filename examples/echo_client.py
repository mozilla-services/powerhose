import random
import sys
import time

from powerhose.client import Client
from powerhose.job import Job
from powerhose.util import set_logger


set_logger(True)
client = Client()

print 'Running 100 echo'

start = time.time()

for i in range(2000):
    data = str(random.randint(1, 1000))
    job = Job(data)
    res = client.execute(job)
    assert res == data
    sys.stdout.write('.')
    sys.stdout.flush()

print 'Done in %.2f' % (time.time() - start)
