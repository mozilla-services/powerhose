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
                            [--heartbeat HEARTBEAT] [--debug] [--check]
                            [--purge-ghosts] [--logfile LOGFILE]

    Powerhose broker.

    optional arguments:
    -h, --help            show this help message and exit
    --frontend FRONTEND   ZMQ socket to receive jobs.
    --backend BACKEND     ZMQ socket for workers.
    --heartbeat HEARTBEAT
                            ZMQ socket for the heartbeat.
    --debug               Debug mode
    --check               Use this option to check if there's a running broker.
                            Returns the PID if a broker is up.
    --purge-ghosts        Use this option to purge ghost brokers.
    --logfile LOGFILE     File to log in to .


**--check** and **--purge-ghosts** are maintenance option that are not running
a broker but just checking an existing broker::

    $ powerhose-broker --check
    [2012-05-25 11:11:28,282][powerhose] A broker is running. PID: 11668

    $ bin/powerhose-broker --purge-ghosts
    [2012-05-25 11:12:09,744][powerhose] The active broker runs at PID: 11668
    [2012-05-25 11:12:09,744][powerhose] No ghosts where killed.

Those options can be used to health check and monitor the broker, which
is the stable node of the Powerhose architecture.


powerhose-worker
----------------

Runs one worker.

::

    $ powerhose-worker --help
    usage: powerhose-worker [-h] [--backend BACKEND] [--debug] [--logfile LOGFILE]
                            [--heartbeat HEARTBEAT] [--params PARAMS]
                            [--timeout TIMEOUT] [--max-age MAX_AGE]
                            [--max-age-delta MAX_AGE_DELTA]
                            target

    Runs a worker.

    positional arguments:
    target                Fully qualified name of the callable.

    optional arguments:
    -h, --help            show this help message and exit
    --backend BACKEND     ZMQ socket to the broker.
    --debug               Debug mode
    --logfile LOGFILE     File to log in to.
    --heartbeat HEARTBEAT
                            ZMQ socket for the heartbeat.
    --params PARAMS       The parameters to be used in the worker.
    --timeout TIMEOUT     The maximum time allowed before the thread stacks is
                            dump and the job result not sent back.
    --max-age MAX_AGE     The maximum age for a worker in seconds. After that
                            delay, the worker will simply quit. When set to -1,
                            never quits.
    --max-age-delta MAX_AGE_DELTA
                            The maximum value in seconds added to max_age


The **--max-age** option is useful when you want your worker to exit after
some time. The typical use case is when you have a program that keeps some
connectors open on some external ressources, and those ressources change over
time.


powerhose
---------

Runs one broker and several workers by using the two previous commands.

::

    $ powerhose --help
    usage: powerhose [-h] [--frontend FRONTEND] [--backend BACKEND]
                    [--heartbeat HEARTBEAT] [--debug]
                    [--numprocesses NUMPROCESSES] [--logfile LOGFILE]
                    target

    Run a Powerhose cluster.

    positional arguments:
    target                Fully qualified name of the callable.

    optional arguments:
    -h, --help            show this help message and exit
    --frontend FRONTEND   ZMQ socket to receive jobs.
    --backend BACKEND     ZMQ socket for workers.
    --heartbeat HEARTBEAT
                            ZMQ socket for the heartbeat.
    --debug               Debug mode
    --numprocesses NUMPROCESSES
                            Number of processes to run.
    --logfile LOGFILE     File to log in to .
