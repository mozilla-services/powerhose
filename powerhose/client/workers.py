from circus import get_arbiter
from powerhose import logger


class Workers(object):
    def __init__(self, cmd, num_workers=5, timeout=1.,
                 check=5., controller='tcp://127.0.0.1:5555', **kw):
        self.arbiter = get_arbiter(cmd, num_workers, timeout,
                                   controller=controller,
                                   check_flapping=False, **kw)

    def run(self):
        logger.debug('starting workers')
        self.arbiter.start()
        logger.debug('workers Stopped')

    def stop(self):
        logger.debug('stopping workers')
        self.arbiter.terminate()
        logger.debug('stopping workers done')
