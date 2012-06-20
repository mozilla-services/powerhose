import random
import sys
import time

from powerhose.client import Client
from powerhose.job import Job
from powerhose.util import set_logger


#set_logger(True)
client = Client()

#print 'Running 100 echo'

start = time.time()

#for i in range(2000):
i = 0

while True:
    data = str(random.randint(1, 1000))
    job = Job(data)
    sys.stdout.write(str(i) +  '-> ')
    sys.stdout.flush()
    res = client.execute(job)
    assert res == data
    sys.stdout.write('OK\n')
    sys.stdout.flush()
    i += 1

print 'Done in %.2f' % (time.time() - start)
