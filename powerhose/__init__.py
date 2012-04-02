# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import logging
import os
import sys
import argparse


logger = logging.getLogger('powerhose')


def get_cluster(target, numprocesses=5, working_dir='.', logfile='stdout',
                debug=False, background=False):
    from circus import get_arbiter

    python = sys.executable
    if debug:
        debug = ' --debug'
    else:
        debug = ''

    broker_cmd = python + ' -m powerhose.broker --logfile ' + logfile + debug
    worker_cmd = (python + ' -m powerhose.worker ' + target + ' --logfile '+
                  logfile + debug)

    watchers = [{'name': 'broker',
                 'cmd': broker_cmd,
                 'working_dir': working_dir,
                 'shell': True,
                 'executable': python,
                 },
                {'name': 'workers',
                 'cmd': worker_cmd,
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

    cluster = get_cluster(args.target, args.numprocesses, logfile=args.logfile,
                          debug=args.debug)
    try:
        cluster.start()
    except KeyboardInterrupt:
        pass
    finally:
        cluster.stop()


if __name__ == '__main__':
    main()
