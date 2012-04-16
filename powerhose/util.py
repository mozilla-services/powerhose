# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import atexit
import time
import zmq
import logging
import logging.handlers
import sys

from powerhose.exc import TimeoutError


DEFAULT_FRONTEND = "ipc:///tmp/powerhose-front.ipc"
DEFAULT_BACKEND = "ipc:///tmp/powerhose-back.ipc"
DEFAULT_HEARTBEAT = "ipc:///tmp/powerhose-beat.ipc"
logger = logging.getLogger('powerhose')
_IPC_FILES = []

PARAMS = {}


@atexit.register
def _cleanup_ipc_files():
    for file in _IPC_FILES:
        file = file.split('ipc://')[-1]
        if os.path.exists(file):
            os.remove(file)


def register_ipc_file(file):
    _IPC_FILES.append(file)


def send(socket, msg, more=False, max_retries=3, retry_sleep=0.1):
    retries = 0
    while retries < max_retries:
        try:
            logger.debug('send')

            if more:
                socket.send(msg, zmq.SNDMORE | zmq.NOBLOCK)
            else:
                socket.send(msg, zmq.NOBLOCK)
            return
        except zmq.ZMQError, e:
            logger.debug('Failed on send()')
            logger.debug(str(e))
            if e.errno in (zmq.EFSM, zmq.EAGAIN):
                retries += 1
                time.sleep(retry_sleep)
            else:
                raise

    logger.debug('Sending failed')
    logger.debug(msg)
    raise TimeoutError()


def recv(socket, max_retries=3, retry_sleep=0.1):
    retries = 0
    while retries < max_retries:
        try:
            logger.debug('receive')
            return socket.recv(zmq.NOBLOCK)
        except zmq.ZMQError, e:
            logger.debug('Failed on recv()')
            logger.debug(str(e))
            if e.errno in (zmq.EFSM, zmq.EAGAIN):
                retries += 1
                time.sleep(retry_sleep)
            else:
                raise

    logger.debug('Receiving failed')
    raise TimeoutError()


def set_logger(debug=False, name='powerhose', logfile='stdout'):
    # setting up the logger
    logger_ = logging.getLogger(name)
    logger_.setLevel(logging.DEBUG)

    if logfile == 'stdout':
        ch = logging.StreamHandler()
    else:
        ch = logging.handlers.RotatingFileHandler(logfile, mode='a+')

    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s][%(name)s] %(message)s')
    ch.setFormatter(formatter)
    logger_.addHandler(ch)


# taken from distutils2
def resolve_name(name):
    """Resolve a name like ``module.object`` to an object and return it.

    This functions supports packages and attributes without depth limitation:
    ``package.package.module.class.class.function.attr`` is valid input.
    However, looking up builtins is not directly supported: use
    ``__builtin__.name``.

    Raises ImportError if importing the module fails or if one requested
    attribute is not found.
    """
    if '.' not in name:
        # shortcut
        __import__(name)
        return sys.modules[name]

    # FIXME clean up this code!
    parts = name.split('.')
    cursor = len(parts)
    module_name = parts[:cursor]
    ret = ''

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name))
            break
        except ImportError:
            cursor -= 1
            module_name = parts[:cursor]

    if ret == '':
        raise ImportError(parts[0])

    for part in parts[1:]:
        try:
            ret = getattr(ret, part)
        except AttributeError, exc:
            raise ImportError(exc)

    return ret


def timed(func):
    def _timed(*args, **kw):
        start = time.time()
        try:
            return func(*args, **kw)
        finally:
            logger.debug('%.4f' % (time.time() - start))
    return _timed


def decode_params(params):
    """Decode a string into a dict. This is mainly useful when passing a dict
    trough the command line.

    The params passed in "params" should be in the form of key:value, separated
    by a pipe, the output is a python dict.
    """
    output_dict = {}
    for items in params.split('|'):
        key, value = items.split(':')
        output_dict[key] = value
    return output_dict


def encode_params(intput_dict):
    """Convert the dict given in input into a string of key:value separated
    with pipes, like spam:yeah|eggs:blah
    """
    return '|'.join([':'.join(i) for i in intput_dict.items()])


def get_params():
    return PARAMS
