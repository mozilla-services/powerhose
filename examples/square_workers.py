from powerhose.client.workers import Workers
import sys

cmd = '%s examples/square_worker.py ipc://worker-routing-$WID.ipc'


workers = Workers(cmd % sys.executable)
try:
    workers.run()
except KeyboardInterrupt:
    workers.stop()
