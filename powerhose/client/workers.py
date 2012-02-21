from circus import get_trainer


class Workers(object):
    def __init__(self, cmd, num_workers=5, timeout=1.,
                 check=5., controller='tcp://127.0.0.1:5555'):
        self.trainer = get_trainer(cmd, num_workers, timeout, check, controller)

    def run(self):
        self.trainer.run()

    def stop(self):
        self.trainer.terminate()
