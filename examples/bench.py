import hmac
import time
import binascii
import os
import sys
import subprocess
import threading

from powerhose import get_cluster
from powerhose.client import Client


_KEY = binascii.b2a_hex(os.urandom(4096))[:4096]


def _sign(data):
    seed = hmac.new(_KEY, data).hexdigest()
    for i in range(400):
        seed = hmac.new(_KEY, seed).hexdigest()
    return 'OK'


def sign(job):
    return _sign(job.data)


_SIZE = 400
_THREADS = 4
_ONE = _SIZE / _THREADS
_PROC = 10


def timed(msg):
    def _timed(func):
        def __timed(*args, **kw):
            sys.stdout.write(msg + '...')
            sys.stdout.flush()
            start = time.time()
            try:
                return func(*args, **kw)
            finally:
                sys.stdout.write('%.4f s\n' % (time.time() - start))
                sys.stdout.flush()
        return __timed
    return _timed


@timed('%d calls, simple.' % _SIZE)
def simple():
    for i in range(_SIZE):
        _sign(str(i))


@timed('%d calls, %d threads' % (_SIZE, _THREADS))
def simple_3():
    def _t():
        for i in range(_ONE):
            _sign(str(i))

    th = [threading.Thread(target=_t) for i in range(_THREADS)]
    for t in th:
        t.start()

    for t in th:
        t.join()


@timed('%d calls via phose, %d threads %d phose workers' % (_SIZE, _THREADS,
    _PROC))
def _phose3():

    def _t():
        client = Client()
        for i in range(_ONE):
            try:
                client.execute(str(i))
            except:
                print 'error'

    th = [threading.Thread(target=_t) for i in range(_THREADS)]
    for t in th:
        t.start()

    for t in th:
        t.join()


@timed('%d calls via phose. %d workers' % (_SIZE, _PROC))
def _phose(client):
    for i in range(_SIZE):
        try:
            client.execute(str(i))
        except:
            print 'error'


def phose():
    client = Client()
    p = run_cluster()
    time.sleep(5.)
    try:
        _phose(client)
    finally:
        p.terminate()


def phose_3():
    p = run_cluster()
    time.sleep(5.)
    try:
        _phose3()
    finally:
        p.terminate()


def _run_cluster():
    cluster = get_cluster('bench.sign', debug=False,
                          numprocesses=_PROC,
                          logfile='/tmp/phose')
    try:
        cluster.start()
    finally:
        cluster.stop()


def run_cluster():
    cmd = sys.executable + ' -c "import bench; bench._run_cluster()"'
    p = subprocess.Popen(cmd, shell=True)
    return p


@timed('Single job')
def single():
    _sign('1')


if __name__ == '__main__':
    single()
    #simple()
    simple_3()
    #phose()
    phose_3()
