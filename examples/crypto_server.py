""" Implements a web server that signs data passed into a POST
"""
from bottle import route, request, default_app
from pycryptopp.publickey import rsa
import time
import threading
import thread

from gevent import monkey
from gevent_zeromq import monkey_patch


from powerhose.client import Pool


monkey.patch_all()
monkey_patch()


class RSA3248(object):

    SIZEINBITS = 3248

    def __init__(self):
        self.signer = rsa.generate(sizeinbits=self.SIZEINBITS)

    def sign(self, msg):
        return self.signer.sign(msg)

crypto = RSA3248()

clients = {}
_cl = Pool()

def sign(job):
    crypto.sign(job.data)
    return 'OK'


@route('/', method='POST')
def index():
    data = request.body.read()
    crypto.sign(data)
    return 'OK'


@route('/phose', method='POST')
def phose():
    data = request.body.read()
    return _cl.execute(data)



application = default_app()


if __name__ == '__main__':
    def _t():
        client = Client()
        for i in range(200):
            client.execute(str(i))

    threads = [threading.Thread(target=_t) for i in range(5)]

    start = time.time()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print time.time() - start
