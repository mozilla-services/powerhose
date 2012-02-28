from circus import get_trainer
from powerhose import logger


class Workers(object):
    def __init__(self, cmd, num_workers=5, timeout=1.,
                 check=5., controller='tcp://127.0.0.1:5555'):
        self.trainer = get_trainer(cmd, num_workers, timeout,
                warmup_delay=check, controller=controller)

    def run(self):
        logger.debug('starting workers')
        self.trainer.start()

    def stop(self):
        logger.debug('stopping workers')
        self.trainer.stop()
        logger.debug('stopping workers done')
