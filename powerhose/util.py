# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import atexit


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
