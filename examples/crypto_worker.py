# taken from pycryptopp
from pycryptopp.publickey import ecdsa, ed25519, rsa
import random as insecurerandom
from powerhose.job import Job


def insecurerandstr(n):
    return ''.join(map(chr, map(insecurerandom.randrange, [0]*n, [256]*n)))



algs = {}


class ECDSA256(object):
    def __init__(self):
        self.seed = insecurerandstr(32)

    def sign(self, msg):
        return signer.sign(msg)

algs['ECDSA256'] = ECDSA256()


class Ed25519(object):
    def __init__(self):
        self.seed = insecurerandstr(32)
        self.signer = ed25519.SigningKey(self.seed)

    def sign(self, msg):
        return self.signer.sign(msg)

algs['Ed25519'] = Ed25519()



class RSA2048(object):
    SIZEINBITS=2048

    def __init__(self):
        self.signer = rsa.generate(sizeinbits=self.SIZEINBITS)

    def sign(self, msg):
        return self.signer.sign(msg)

algs['RSA2048'] = RSA2048()


class RSA3248(object):
    SIZEINBITS=3248

    def __init__(self):
        self.signer = rsa.generate(sizeinbits=self.SIZEINBITS)

    def sign(self, msg):
        return self.signer.sign(msg)


algs['RSA3248'] = RSA3248()


def sign(job):
    msg, alg = job.data.split('--')
    ob = algs[alg]
    return ob.sign(msg)


if __name__ == '__main__':
    job = Job('somedata--RSA2048')
    print sign(job)
