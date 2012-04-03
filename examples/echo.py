from powerhose import get_cluster
from powerhose.client import Client


cluster = get_cluster('echo_worker.echo', background=True)
cluster.start()

client = Client()

for i in range(10):
    print client.execute(str(i))

cluster.stop()
