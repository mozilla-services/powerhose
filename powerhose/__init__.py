# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
import argparse

from powerhose.util import (DEFAULT_BACKEND, DEFAULT_HEARTBEAT,
                            DEFAULT_FRONTEND, logger)


def get_cluster(target, numprocesses=5, frontend=DEFAULT_FRONTEND,
                backend=DEFAULT_BACKEND, heartbeat=DEFAULT_HEARTBEAT,
                working_dir='.', logfile='stdout',
                debug=False, background=False):
    """Runs a Powerhose cluster.

    Options:

    - **callable**: The Python callable that will be called when the broker
      receive a job.
    - **numprocesses**: The number of workers. Defaults to 5.
    - **frontend**: the ZMQ socket to receive jobs.
    - **backend**: the ZMQ socket to communicate with workers.
    - **heartbeat**: the ZMQ socket to receive heartbeat requests/
    - **working_dir**: The working directory. Defaults to *"."*
    - **logfile**: The file to log into. Defaults to stdout.
    - **debug**: If True, the logs are at the DEBUG level. Defaults to False
    - **background**: If True, the cluster is run in the background. Defaults to
      False.
    """
    from circus import get_arbiter

    python = sys.executable
    if debug:
        debug = ' --debug'
    else:
        debug = ''

    broker_cmd = [python, '-m', 'powerhose.broker', '--logfile',  logfile,
                  debug, '--frontend', frontend, '--backend', backend,
                  '--heartbeat', heartbeat]

    worker_cmd = [python, '-m', 'powerhose.worker', target, '--logfile',
                  logfile, debug, '--backend', backend, '--heartbeat',
                  heartbeat]

    watchers = [{'name': 'broker',
                 'cmd': ' '.join(broker_cmd),
                 'working_dir': working_dir,
                 'shell': True,
                 'executable': python,
                 },
                {'name': 'workers',
                 'cmd': ' '.join(worker_cmd),
                 'numprocesses': numprocesses,
                 'working_dir': working_dir,
                 'shell': True,
                 'executable': python,
                 }
                ]

    # XXX add more options
    return get_arbiter(watchers, background=background)


def main(args=sys.argv):
    from powerhose.util import set_logger, resolve_name

    parser = argparse.ArgumentParser(description='Run a Powerhose cluster.')

    parser.add_argument('--frontend', dest='frontend',
                        default=DEFAULT_FRONTEND,
                        help="ZMQ socket to receive jobs.")

    parser.add_argument('--backend', dest='backend',
                        default=DEFAULT_BACKEND,
                        help="ZMQ socket for workers.")

    parser.add_argument('--heartbeat', dest='heartbeat',
                        default=DEFAULT_HEARTBEAT,
                        help="ZMQ socket for the heartbeat.")

    parser.add_argument('target', help="Fully qualified name of the callable.")

    parser.add_argument('--debug', action='store_true', default=False,
                        help="Debug mode")

    parser.add_argument('--numprocesses', dest='numprocesses', default=5,
                        help="Number of processes to run.")

    parser.add_argument('--logfile', dest='logfile', default='stdout',
                        help="File to log in to .")

    args = parser.parse_args()

    set_logger(args.debug, 'powerhose', args.logfile)
    set_logger(args.debug, 'circus', args.logfile)
    sys.path.insert(0, os.getcwd())  # XXX
    resolve_name(args.target)  # check the callable

    cluster = get_cluster(args.target, args.numprocesses,
                          frontend=args.frontend, backend=args.backend,
                          heartbeat=args.heartbeat, logfile=args.logfile,
                          debug=args.debug)
    try:
        cluster.start()
    except KeyboardInterrupt:
        pass
    finally:
        cluster.stop()


if __name__ == '__main__':
    main()
