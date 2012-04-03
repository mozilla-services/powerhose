""" Implements a web server that signs data passed into a POST
"""
from bottle import route, run, request, default_app
from pycryptopp.publickey import rsa
import time

import binascii
import os
import sys

from powerhose import get_cluster
from powerhose.client import Client


class RSA3248(object):
    SIZEINBITS=3248

    def __init__(self):
        self.signer = rsa.generate(sizeinbits=self.SIZEINBITS)

    def sign(self, msg):
        return self.signer.sign(msg)

crypto = RSA3248()

def sign(job):
    return crypto.sign(job.data)


@route('/', method='POST')
def index():
    data = request.body.read()
    return crypto.sign(data)

@route('/phose', method='POST')
def phose():
    data = request.body.read()
    return client.execute(data)


client = Client()
application = default_app()

if __name__ == '__main__':
    #client = Client()

    #cluster = get_cluster('crypto_server.sign', background=True)
    #cluster.start()
    #time.sleep(1.)
    #try:
    #    run(host='localhost', port=8080)   #, server='paste')
    #finally#:
    #    #cluster.stop()
    #    pass
    pass

