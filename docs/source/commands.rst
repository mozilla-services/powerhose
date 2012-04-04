.. _commands:

Command-line tools
==================

Powerhose comes with three commands:

- **powerhose-broker**: runs a broker.
- **powerhose-worker**: runs a *python* worker.
- **powerhose**: runs a broker *and* some workers.

To run a Powerhose cluster, you need to run a broker and
some workers. So you would use **powerhose** *or*
**powerhose-broker** and some **powerhose-worker**.

powerhose-broker
----------------

Runs a Powerhose broker::

    $ powerhose-broker --help
    usage: powerhose-broker [-h] [--frontend FRONTEND] [--backend BACKEND]
                            [--heartbeat HEARTBEAT] [--debug] [--logfile LOGFILE]

    Powerhose broker.

    optional arguments:
    -h, --help            show this help message and exit
    --frontend FRONTEND   ZMQ socket to receive jobs.
    --backend BACKEND     ZMQ socket for workers.
    --heartbeat HEARTBEAT
                            ZMQ socket for the heartbeat.
    --debug               Debug mode
    --logfile LOGFILE     File to log in to .


powerhose-worker
----------------

Runs one worker.

::

    $ powerhose-worker --help
    usage: powerhose-worker [-h] [--backend BACKEND] [--debug] [--logfile LOGFILE]
                            [--heartbeat HEARTBEAT]
                            target

    Run some watchers.

    positional arguments:
    target                Fully qualified name of the callable.

    optional arguments:
    -h, --help            show this help message and exit
    --backend BACKEND     ZMQ socket to the broker.
    --debug               Debug mode
    --logfile LOGFILE     File to log in to .
    --heartbeat HEARTBEAT
                            ZMQ socket for the heartbeat


powerhose
---------

Runs one broker and several workers by using the two previous commands.

::

    $ powerhose --help
    usage: powerhose [-h] [--debug] [--numprocesses NUMPROCESSES]
                    [--logfile LOGFILE]
                    target

    Run a Powerhose cluster.

    positional arguments:
    target                Fully qualified name of the callable.

    optional arguments:
    -h, --help            show this help message and exit
    --debug               Debug mode
    --numprocesses NUMPROCESSES
                            Number of processes to run.
    --logfile LOGFILE     File to log in to

