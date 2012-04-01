# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import atexit
import time
import zmq
import logging

from powerhose import logger
from powerhose.exc import TimeoutError

_SEP = '*****'


# will do better later
def serialize(*seq):
    for part in seq:
        if _SEP in part:
            raise NotImplementedError
    return _SEP.join(seq)


def unserialize(data):
    return data.split(_SEP)


_IPC_FILES = []


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

    raise TimeoutError()


def recv(socket, max_retries=3, retry_sleep=0.1):
    retries = 0
    while retries < max_retries:
        try:
            return socket.recv(zmq.NOBLOCK)
        except zmq.ZMQError, e:
            logger.debug('Failed on recv()')
            logger.debug(str(e))
            if e.errno in (zmq.EFSM, zmq.EAGAIN):
                retries += 1
                time.sleep(retry_sleep)
            else:
                raise

    raise TimeoutError()


def set_logger(debug=False):
    # setting up the logger
    logger_ = logging.getLogger('powerhose')
    logger_.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    if debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)

    formatter = logging.Formatter('[%(asctime)s][%(name)s] %(message)s')
    ch.setFormatter(formatter)
    logger_.addHandler(ch)
