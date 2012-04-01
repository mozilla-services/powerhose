from powerhose.util import set_logger
from powerhose import get_cluster


set_logger(True)
cluster = get_cluster('crypto_worker.sign')
try:
    cluster.start()
finally:
    cluster.stop()
